/**
 * KnowledgeTree Dashboard Page
 * Main landing page after authentication
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { LanguageSwitcher } from '@/components/language-switcher';
import { ThemeToggle } from '@/components/theme-toggle';
import { useTranslation } from 'react-i18next';
import { FolderOpen, FileText, Search, MessageSquare, Loader2, CreditCard, Crown, Globe } from 'lucide-react';
import { projectsApi, chatApi, subscriptionsApi } from '@/lib/api';
import type { Project } from '@/types/api';
import type { SubscriptionDetails } from '@/types/subscription';

export function DashboardPage() {
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  // State for statistics
  const [stats, setStats] = useState({
    projects: 0,
    documents: 0,
    conversations: 0,
  });
  const [subscription, setSubscription] = useState<SubscriptionDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Fetch dashboard statistics and subscription
  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        setError('');

        // Fetch all data in parallel
        const [projectsResponse, subscriptionResponse] = await Promise.all([
          projectsApi.list(1, 100),
          subscriptionsApi.getMySubscription().catch(() => null),
        ]);

        const projects: Project[] = projectsResponse.data.projects;
        const projectCount = projects.length;

        // Sum all documents from all projects
        const documentCount = projects.reduce((sum, project) => sum + (project.document_count || 0), 0);

        // Fetch conversation counts for each project (parallel)
        const conversationPromises = projects.map(project =>
          chatApi.listConversations(project.id, 1, 1)
            .then(res => res.data.total)
            .catch(() => 0) // If project has no conversations, return 0
        );

        const conversationCounts = await Promise.all(conversationPromises);
        const conversationCount = conversationCounts.reduce((sum, count) => sum + count, 0);

        setStats({
          projects: projectCount,
          documents: documentCount,
          conversations: conversationCount,
        });

        // Set subscription if available
        if (subscriptionResponse?.data) {
          setSubscription(subscriptionResponse.data);
        }
      } catch (err) {
        console.error('Failed to fetch dashboard statistics:', err);
        setError(err instanceof Error ? err.message : t('dashboard.errors.loadFailed'));
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  return (
    <div className="min-h-screen bg-neutral-50 dark:bg-neutral-900">
      {/* Header */}
      <header className="border-b border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-950">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
                {t('app.name')}
              </h1>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-neutral-600 dark:text-neutral-400">
                {user?.email}
              </span>
              <LanguageSwitcher />
              <ThemeToggle />
              <Button variant="outline" onClick={logout}>
                {t('common.signOut')}
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-6">
          {/* Welcome Section */}
          <div>
            <h2 className="text-3xl font-bold text-neutral-900 dark:text-neutral-50">
              {t('dashboard.welcome', 'Welcome')}, {user?.full_name || user?.email}!
            </h2>
            <p className="text-neutral-600 dark:text-neutral-400 mt-2">
              {t('dashboard.subtitle', 'Manage your knowledge base with AI and RAG system')}
            </p>
          </div>

          {/* Quick Stats */}
          {error && (
            <div className="bg-error-50 dark:bg-error-900/20 border border-error-200 dark:border-error-800 rounded-lg p-4">
              <p className="text-error-800 dark:text-error-200 text-sm">{error}</p>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FolderOpen className="h-5 w-5" />
                  Projekty
                </CardTitle>
                <CardDescription>Twoje projekty wiedzy</CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="flex items-center gap-2">
                    <Loader2 className="h-6 w-6 animate-spin text-neutral-400" />
                    <span className="text-neutral-600 dark:text-neutral-400">Ładowanie...</span>
                  </div>
                ) : (
                  <>
                    <div className="text-4xl font-bold text-primary-600 dark:text-primary-400">
                      {stats.projects}
                    </div>
                    <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-2">
                      {stats.projects === 0 ? 'Brak projektów' :
                       stats.projects === 1 ? '1 projekt' :
                       `${stats.projects} projektów`}
                    </p>
                  </>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  Dokumenty
                </CardTitle>
                <CardDescription>Przesłane pliki</CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="flex items-center gap-2">
                    <Loader2 className="h-6 w-6 animate-spin text-neutral-400" />
                    <span className="text-neutral-600 dark:text-neutral-400">Ładowanie...</span>
                  </div>
                ) : (
                  <>
                    <div className="text-4xl font-bold text-primary-600 dark:text-primary-400">
                      {stats.documents}
                    </div>
                    <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-2">
                      {stats.documents === 0 ? 'Brak dokumentów' :
                       stats.documents === 1 ? '1 dokument' :
                       `${stats.documents} dokumentów`}
                    </p>
                  </>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="h-5 w-5" />
                  Rozmowy
                </CardTitle>
                <CardDescription>Czaty z AI</CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="flex items-center gap-2">
                    <Loader2 className="h-6 w-6 animate-spin text-neutral-400" />
                    <span className="text-neutral-600 dark:text-neutral-400">Ładowanie...</span>
                  </div>
                ) : (
                  <>
                    <div className="text-4xl font-bold text-primary-600 dark:text-primary-400">
                      {stats.conversations}
                    </div>
                    <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-2">
                      {stats.conversations === 0 ? 'Brak rozmów' :
                       stats.conversations === 1 ? '1 rozmowa' :
                       `${stats.conversations} rozmów`}
                    </p>
                  </>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Subscription & Usage */}
          {subscription && (
            <Card className={subscription.plan === 'free' ? 'border-primary-500 dark:border-primary-400' : ''}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Crown className={`h-5 w-5 ${subscription.plan !== 'free' ? 'text-yellow-500' : 'text-neutral-400'}`} />
                    <CardTitle>
                      {subscription.plan === 'free' ? 'Plan Free' :
                       subscription.plan === 'starter' ? 'Plan Starter' :
                       subscription.plan === 'professional' ? 'Plan Professional' :
                       'Plan Enterprise'}
                    </CardTitle>
                  </div>
                  {subscription.plan === 'free' && (
                    <Button onClick={() => navigate('/billing')} size="sm">
                      <CreditCard className="mr-2 h-4 w-4" />
                      {t('dashboard.upgrade', 'Upgrade')}
                    </Button>
                  )}
                </div>
                <CardDescription>
                  {subscription.plan === 'free' ? 'Limity darmowego planu' :
                   `Twój obecny plan - ${subscription.plan_details?.name || subscription.plan}`}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {/* Messages */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-neutral-600 dark:text-neutral-400">Wiadomości</span>
                      <span className="font-medium">
                        {subscription.messages_sent || 0} / {subscription.plan_details?.messages_limit || '∞'}
                      </span>
                    </div>
                    {subscription.plan_details?.messages_limit && (
                      <div className="w-full bg-neutral-200 dark:bg-neutral-700 rounded-full h-2">
                        <div
                          className="bg-primary-600 dark:bg-primary-400 h-2 rounded-full transition-all"
                          style={{
                            width: `${Math.min(
                              ((subscription.messages_sent || 0) / subscription.plan_details.messages_limit) * 100,
                              100
                            )}%`
                          }}
                        />
                      </div>
                    )}
                  </div>

                  {/* Storage */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-neutral-600 dark:text-neutral-400">Przestrzeń</span>
                      <span className="font-medium">
                        {subscription.storage_used_mb ? `${(subscription.storage_used_mb / 1024).toFixed(1)} GB` : '0 GB'} / {subscription.plan_details?.storage_gb || '∞'} GB
                      </span>
                    </div>
                    {subscription.plan_details?.storage_gb && (
                      <div className="w-full bg-neutral-200 dark:bg-neutral-700 rounded-full h-2">
                        <div
                          className="bg-primary-600 dark:bg-primary-400 h-2 rounded-full transition-all"
                          style={{
                            width: `${Math.min(
                              ((subscription.storage_used_mb || 0) / 1024 / subscription.plan_details.storage_gb) * 100,
                              100
                            )}%`
                          }}
                        />
                      </div>
                    )}
                  </div>

                  {/* Documents */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-neutral-600 dark:text-neutral-400">Dokumenty</span>
                      <span className="font-medium">
                        {subscription.documents_uploaded || 0} / {subscription.plan_details?.documents_limit || '∞'}
                      </span>
                    </div>
                    {subscription.plan_details?.documents_limit && (
                      <div className="w-full bg-neutral-200 dark:bg-neutral-700 rounded-full h-2">
                        <div
                          className="bg-primary-600 dark:bg-primary-400 h-2 rounded-full transition-all"
                          style={{
                            width: `${Math.min(
                              ((subscription.documents_uploaded || 0) / subscription.plan_details.documents_limit) * 100,
                              100
                            )}%`
                          }}
                        />
                      </div>
                    )}
                  </div>
                </div>

                {/* Plan features */}
                {subscription.plan_details?.features && subscription.plan_details.features.length > 0 && (
                  <div className="mt-6 pt-4 border-t border-neutral-200 dark:border-neutral-800">
                    <p className="text-sm font-medium mb-2">Funkcje planu:</p>
                    <ul className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm text-neutral-600 dark:text-neutral-400">
                      {subscription.plan_details.features.map((feature, idx) => (
                        <li key={idx} className="flex items-center gap-2">
                          <span className="text-green-500">✓</span>
                          {feature}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Trial warning */}
                {subscription.status === 'trialing' && subscription.trial_end && (
                  <div className="mt-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
                    <p className="text-sm text-yellow-800 dark:text-yellow-200">
                      ⏰ Okres próbny kończy się {new Date(subscription.trial_end).toLocaleDateString('pl-PL')}
                    </p>
                  </div>
                )}

                {/* Cancellation warning */}
                {subscription.cancel_at_period_end && subscription.current_period_end && (
                  <div className="mt-4 p-3 bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg">
                    <p className="text-sm text-orange-800 dark:text-orange-200">
                      Subskrypcja zostanie anulowana {new Date(subscription.current_period_end).toLocaleDateString('pl-PL')}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Getting Started */}
          <Card>
            <CardHeader>
              <CardTitle>{t('dashboard.gettingStarted.title', 'Getting Started')}</CardTitle>
              <CardDescription>{t('dashboard.gettingStarted.description', 'Quick access to main features')}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between p-3 border border-neutral-200 dark:border-neutral-800 rounded">
                <div>
                  <p className="font-medium text-neutral-900 dark:text-neutral-50">
                    {t('dashboard.gettingStarted.projects.title', 'Project Management')}
                  </p>
                  <p className="text-sm text-neutral-600 dark:text-neutral-400">
                    {t('dashboard.gettingStarted.projects.description', 'Create and manage knowledge projects')}
                  </p>
                </div>
                <Button onClick={() => navigate('/projects')}>
                  <FolderOpen className="mr-2 h-4 w-4" />
                  {t('dashboard.gettingStarted.goButton', 'Go')}
                </Button>
              </div>

              <div className="flex items-center justify-between p-3 border border-neutral-200 dark:border-neutral-800 rounded">
                <div>
                  <p className="font-medium text-neutral-900 dark:text-neutral-50">
                    {t('dashboard.gettingStarted.documents.title', 'Document Upload')}
                  </p>
                  <p className="text-sm text-neutral-600 dark:text-neutral-400">
                    {t('dashboard.gettingStarted.documents.description', 'Upload PDF files and documents')}
                  </p>
                </div>
                <Button onClick={() => navigate('/documents')}>
                  <FileText className="mr-2 h-4 w-4" />
                  {t('dashboard.gettingStarted.goButton', 'Go')}
                </Button>
              </div>

              <div className="flex items-center justify-between p-3 border border-neutral-200 dark:border-neutral-800 rounded">
                <div>
                  <p className="font-medium text-neutral-900 dark:text-neutral-50">
                    {t('dashboard.gettingStarted.search.title', 'Semantic Search')}
                  </p>
                  <p className="text-sm text-neutral-600 dark:text-neutral-400">
                    {t('dashboard.gettingStarted.search.description', 'Search your knowledge base')}
                  </p>
                </div>
                <Button onClick={() => navigate('/search')}>
                  <Search className="mr-2 h-4 w-4" />
                  {t('dashboard.gettingStarted.goButton', 'Go')}
                </Button>
              </div>

              <div className="flex items-center justify-between p-3 border border-neutral-200 dark:border-neutral-800 rounded">
                <div>
                  <p className="font-medium text-neutral-900 dark:text-neutral-50">
                    Web Crawling
                  </p>
                  <p className="text-sm text-neutral-600 dark:text-neutral-400">
                    Pobieraj treści ze stron internetowych
                  </p>
                </div>
                <Button onClick={() => navigate('/crawl')}>
                  <Globe className="mr-2 h-4 w-4" />
                  {t('dashboard.gettingStarted.goButton', 'Go')}
                </Button>
              </div>

              <div className="flex items-center justify-between p-3 border border-neutral-200 dark:border-neutral-800 rounded">
                <div>
                  <p className="font-medium text-neutral-900 dark:text-neutral-50">
                    {t('dashboard.gettingStarted.chat.title', 'RAG Chat')}
                  </p>
                  <p className="text-sm text-neutral-600 dark:text-neutral-400">
                    {t('dashboard.gettingStarted.chat.description', 'Chat with AI about your documents')}
                  </p>
                </div>
                <Button onClick={() => navigate('/chat')}>
                  <MessageSquare className="mr-2 h-4 w-4" />
                  {t('dashboard.gettingStarted.goButton', 'Go')}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
