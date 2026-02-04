/**
 * Account Page - Subscription and Usage Management
 * Displays current plan, usage statistics, and billing options
 */

import { useTranslation } from 'react-i18next';
import { useSubscription } from '../context/SubscriptionContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Progress } from '../components/ui/progress';
import { Loader2, CheckCircle2, XCircle, AlertTriangle, CreditCard, TrendingUp } from 'lucide-react';
import { PLAN_LABELS, STATUS_LABELS } from '../types/subscription';
import { useNavigate } from 'react-router-dom';
import { useToast } from '../hooks/use-toast';
import api from '../lib/api';
import { useState } from 'react';

export default function AccountPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { toast } = useToast();
  const { subscription, usage, loading, isDemoMode, refreshSubscription } = useSubscription();
  const [isProcessing, setIsProcessing] = useState(false);

  const handleUpgrade = () => {
    navigate('/pricing');
  };

  const handleBillingPortal = async () => {
    if (isDemoMode) {
      toast({
        title: t('account.demoMode'),
        description: t('account.demoModeDescription'),
        variant: 'default',
      });
      return;
    }

    setIsProcessing(true);
    try {
      const response = await api.post('/subscriptions/billing-portal', {
        return_url: window.location.href,
      });
      window.location.href = response.data.portal_url;
    } catch (error: any) {
      toast({
        title: t('error'),
        description: error.response?.data?.detail || t('account.billingPortalError'),
        variant: 'destructive',
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleCancelSubscription = async () => {
    if (isDemoMode) return;

    const confirmed = window.confirm(t('account.cancelConfirm'));
    if (!confirmed) return;

    setIsProcessing(true);
    try {
      await api.post('/subscriptions/cancel', null, {
        params: { at_period_end: true },
      });
      toast({
        title: t('success'),
        description: t('account.cancelSuccess'),
      });
      await refreshSubscription();
    } catch (error: any) {
      toast({
        title: t('error'),
        description: error.response?.data?.detail || t('account.cancelError'),
        variant: 'destructive',
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
      case 'trialing':
        return <CheckCircle2 className="w-4 h-4 text-green-600" />;
      case 'canceled':
      case 'incomplete':
      case 'incomplete_expired':
      case 'past_due':
        return <XCircle className="w-4 h-4 text-red-600" />;
      case 'paused':
        return <AlertTriangle className="w-4 h-4 text-yellow-600" />;
      default:
        return null;
    }
  };

  const getStatusBadgeVariant = (status: string): "default" | "secondary" | "destructive" | "outline" => {
    switch (status) {
      case 'active':
      case 'trialing':
        return 'default';
      case 'canceled':
      case 'incomplete':
      case 'incomplete_expired':
      case 'past_due':
        return 'destructive';
      default:
        return 'secondary';
    }
  };

  const formatUsageValue = (used: number, limit: number | null, metric: string): string => {
    if (limit === null) return `${used} / ∞`;

    if (metric === 'storage') {
      const usedGB = (used / 1024).toFixed(2);
      return `${usedGB} GB / ${limit} GB`;
    }

    return `${used} / ${limit}`;
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!subscription || !usage) {
    return (
      <div className="flex justify-center items-center h-screen">
        <p className="text-muted-foreground">{t('account.noData')}</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 max-w-5xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">{t('account.title')}</h1>
        <p className="text-muted-foreground">{t('account.subtitle')}</p>
      </div>

      {/* Demo Mode Banner */}
      {isDemoMode && (
        <Card className="mb-6 border-blue-500 bg-blue-50 dark:bg-blue-950">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-blue-700 dark:text-blue-300">
              <TrendingUp className="w-5 h-5" />
              {t('account.demoMode')}
            </CardTitle>
            <CardDescription className="text-blue-600 dark:text-blue-400">
              {t('account.demoModeDescription')}
            </CardDescription>
          </CardHeader>
        </Card>
      )}

      {/* Current Plan */}
      <Card className="mb-6">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                {t('account.currentPlan')}
                <Badge variant={getStatusBadgeVariant(subscription.status)}>
                  {STATUS_LABELS[subscription.status]}
                </Badge>
              </CardTitle>
              <CardDescription>
                {PLAN_LABELS[subscription.plan]} {subscription.plan_details.price > 0 && (
                  <span>
                    - ${subscription.plan_details.price}/{subscription.plan_details.interval}
                  </span>
                )}
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              {getStatusIcon(subscription.status)}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Plan Features */}
            <div>
              <h3 className="font-semibold mb-2">{t('account.features')}</h3>
              <ul className="space-y-1">
                {subscription.plan_details.features.map((feature, index) => (
                  <li key={index} className="flex items-center gap-2 text-sm">
                    <CheckCircle2 className="w-4 h-4 text-green-600" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-2 pt-4">
              {subscription.plan !== 'enterprise' && !isDemoMode && (
                <Button onClick={handleUpgrade} className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4" />
                  {t('account.upgrade')}
                </Button>
              )}
              {!isDemoMode && (
                <Button
                  variant="outline"
                  onClick={handleBillingPortal}
                  disabled={isProcessing}
                  className="flex items-center gap-2"
                >
                  {isProcessing ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <CreditCard className="w-4 h-4" />
                  )}
                  {t('account.manageBilling')}
                </Button>
              )}
              {subscription.status === 'active' && !isDemoMode && (
                <Button
                  variant="destructive"
                  onClick={handleCancelSubscription}
                  disabled={isProcessing}
                >
                  {isProcessing ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    t('account.cancel')
                  )}
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Usage Statistics */}
      <Card>
        <CardHeader>
          <CardTitle>{t('account.usage')}</CardTitle>
          <CardDescription>{t('account.usageDescription')}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {/* Messages Usage */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium">{t('account.messages')}</span>
                <span className="text-sm text-muted-foreground">
                  {formatUsageValue(usage.messages.used, usage.messages.limit, 'messages')}
                </span>
              </div>
              <Progress
                value={usage.messages.limit ? (usage.messages.used / usage.messages.limit) * 100 : 0}
                className="h-2"
              />
              {!usage.messages.allowed && (
                <p className="text-xs text-red-600 mt-1">{t('account.limitReached')}</p>
              )}
            </div>

            {/* Documents Usage */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium">{t('account.documents')}</span>
                <span className="text-sm text-muted-foreground">
                  {formatUsageValue(usage.documents.used, usage.documents.limit, 'documents')}
                </span>
              </div>
              <Progress
                value={usage.documents.limit ? (usage.documents.used / usage.documents.limit) * 100 : 0}
                className="h-2"
              />
              {!usage.documents.allowed && (
                <p className="text-xs text-red-600 mt-1">{t('account.limitReached')}</p>
              )}
            </div>

            {/* Storage Usage */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium">{t('account.storage')}</span>
                <span className="text-sm text-muted-foreground">
                  {formatUsageValue(usage.storage.used, usage.storage.limit, 'storage')}
                </span>
              </div>
              <Progress
                value={usage.storage.limit ? (usage.storage.used / usage.storage.limit) * 100 : 0}
                className="h-2"
              />
              {!usage.storage.allowed && (
                <p className="text-xs text-red-600 mt-1">{t('account.limitReached')}</p>
              )}
            </div>

            {/* Projects Usage */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium">{t('account.projects')}</span>
                <span className="text-sm text-muted-foreground">
                  {formatUsageValue(usage.projects.used, usage.projects.limit, 'projects')}
                </span>
              </div>
              <Progress
                value={usage.projects.limit ? (usage.projects.used / usage.projects.limit) * 100 : 0}
                className="h-2"
              />
              {!usage.projects.allowed && (
                <p className="text-xs text-red-600 mt-1">{t('account.limitReached')}</p>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
