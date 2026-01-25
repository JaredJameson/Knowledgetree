/**
 * KnowledgeTree - AI Insights Page
 * AI-powered document and project insights
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Lightbulb,
  Brain,
  FileText,
  FolderTree,
  TrendingUp,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Sparkles,
  Target,
  Layers,
  ArrowRight,
  RefreshCw,
} from 'lucide-react';
import { insightsApi, projectsApi } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';

interface Project {
  id: number;
  name: string;
  description?: string;
  documents_count?: number;
}

interface DocumentInsight {
  document_id: number;
  title: string;
  summary: string;
  key_findings: string[];
  topics: string[];
  entities: string[];
  sentiment: string;
  action_items: string[];
  importance_score: number;
  generated_at: string;
}

interface ProjectInsight {
  project_id: number;
  project_name: string;
  executive_summary: string;
  total_documents: number;
  key_themes: string[];
  top_categories: Array<{ name: string; documents: number }>;
  document_summaries: DocumentInsight[];
  patterns: string[];
  recommendations: string[];
  generated_at: string;
}

export default function InsightsPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { toast } = useToast();

  // State
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [available, setAvailable] = useState(true);

  // Project insights
  const [projectInsights, setProjectInsights] = useState<ProjectInsight | null>(null);
  const [generatingProject, setGeneratingProject] = useState(false);

  // Document insights
  const [selectedDocumentId, setSelectedDocumentId] = useState<number | null>(null);
  const [documentInsights, setDocumentInsights] = useState<DocumentInsight | null>(null);
  const [generatingDocument, setGeneratingDocument] = useState(false);

  // Settings
  const [maxDocuments, setMaxDocuments] = useState(10);
  const [includeCategories, setIncludeCategories] = useState(true);

  // Load projects on mount
  useEffect(() => {
    loadProjects();
    checkAvailability();
  }, []);

  const loadProjects = async () => {
    try {
      const response = await projectsApi.list(1, 100);
      setProjects(response.data.projects || []);
      if (response.data.projects?.length > 0 && !selectedProject) {
        setSelectedProject(response.data.projects[0].id);
      }
    } catch (error) {
      toast({
        title: 'Błąd',
        description: 'Nie udało się załadować projektów',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const checkAvailability = async () => {
    try {
      const response = await insightsApi.availability();
      setAvailable(response.data.available);
    } catch (error) {
      console.error('Failed to check insights availability:', error);
    }
  };

  const handleGenerateProjectInsights = async () => {
    if (!selectedProject) {
      toast({
        title: 'Błąd',
        description: 'Wybierz projekt',
        variant: 'destructive',
      });
      return;
    }

    setGeneratingProject(true);
    setProjectInsights(null);

    try {
      const response = await insightsApi.generateProjectInsights({
        max_documents: maxDocuments,
        include_categories: includeCategories,
        force_refresh: true,
      });

      setProjectInsights(response.data);
      toast({
        title: 'Sukces',
        description: 'Wygenerowano wnioski projektowe',
      });
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Nie udało się wygenerować wniosków';
      toast({
        title: 'Błąd',
        description: message,
        variant: 'destructive',
      });
      if (message.includes('not enabled')) {
        setAvailable(false);
      }
    } finally {
      setGeneratingProject(false);
    }
  };

  const handleGenerateDocumentInsights = async () => {
    if (!selectedDocumentId) {
      toast({
        title: 'Błąd',
        description: 'Wprowadź ID dokumentu',
        variant: 'destructive',
      });
      return;
    }

    setGeneratingDocument(true);
    setDocumentInsights(null);

    try {
      const response = await insightsApi.generateDocumentInsights(
        selectedDocumentId,
        true
      );

      setDocumentInsights(response.data);
      toast({
        title: 'Sukces',
        description: 'Wygenerowano wnioski dla dokumentu',
      });
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Nie udało się wygenerować wniosków';
      toast({
        title: 'Błąd',
        description: message,
        variant: 'destructive',
      });
      if (message.includes('not enabled')) {
        setAvailable(false);
      }
    } finally {
      setGeneratingDocument(false);
    }
  };

  const getSentimentColor = (sentiment: string) => {
    const colors = {
      positive: 'bg-success-500',
      neutral: 'bg-neutral-500',
      negative: 'bg-error-500',
      mixed: 'bg-warning-500',
    };
    return colors[sentiment as keyof typeof colors] || 'bg-neutral-500';
  };

  const getSentimentLabel = (sentiment: string) => {
    const labels = {
      positive: 'Pozytywny',
      neutral: 'Neutralny',
      negative: 'Negatywny',
      mixed: 'Mieszany',
    };
    return labels[sentiment as keyof typeof labels] || sentiment;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-primary-500" />
      </div>
    );
  }

  if (!available) {
    return (
      <div className="container mx-auto py-8 px-4 max-w-4xl">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            AI Insights jest wyłączona. Skontaktuj się z administratorem lub włącz
            funkcję w konfiguracji (ENABLE_AI_INSIGHTS).
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4 max-w-7xl">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
            <Brain className="h-6 w-6 text-purple-600 dark:text-purple-400" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-neutral-900 dark:text-neutral-50">
              AI Insights
            </h1>
            <p className="text-neutral-600 dark:text-neutral-400">
              Analizuj dokumenty i projekty z pomocą sztucznej inteligencji
            </p>
          </div>
        </div>
      </div>

      {/* Project selector */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FolderTree className="h-5 w-5" />
            Wybierz projekt
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2 flex-wrap">
            {projects.map((project) => (
              <Button
                key={project.id}
                variant={selectedProject === project.id ? 'default' : 'outline'}
                onClick={() => setSelectedProject(project.id)}
              >
                <FileText className="h-4 w-4 mr-2" />
                {project.name}
                {project.documents_count !== undefined && (
                  <Badge variant="secondary" className="ml-2">
                    {project.documents_count}
                  </Badge>
                )}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Main content tabs */}
      <Tabs defaultValue="project" className="space-y-6">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="project">Projektowe wnioski</TabsTrigger>
          <TabsTrigger value="document">Wnioski z dokumentu</TabsTrigger>
        </TabsList>

        {/* Project Insights Tab */}
        <TabsContent value="project" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Generuj wnioski z całego projektu</CardTitle>
              <CardDescription>
                Analizuje wiele dokumentów, aby znaleźć tematy, wzorce i rekomendacje
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Settings */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium">
                    Maks. dokumentów: {maxDocuments}
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="50"
                    value={maxDocuments}
                    onChange={(e) => setMaxDocuments(Number(e.target.value))}
                    className="w-full mt-2"
                    disabled={generatingProject}
                  />
                </div>

                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="includeCategories"
                    checked={includeCategories}
                    onChange={(e) => setIncludeCategories(e.target.checked)}
                    disabled={generatingProject}
                    className="rounded"
                  />
                  <label htmlFor="includeCategories" className="cursor-pointer text-sm">
                    Uwzględnij kategorie
                  </label>
                </div>
              </div>

              {/* Generate button */}
              <Button
                onClick={handleGenerateProjectInsights}
                disabled={generatingProject || !selectedProject}
                className="w-full"
                size="lg"
              >
                {generatingProject ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Generowanie...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4 mr-2" />
                    Generuj wnioski projektowe
                  </>
                )}
              </Button>

              {/* Results */}
              {projectInsights && (
                <>
                  <Separator />
                  <div className="space-y-6">
                    {/* Executive Summary */}
                    <div>
                      <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
                        <Target className="h-5 w-5 text-purple-500" />
                        Executive Summary
                      </h3>
                      <p className="text-neutral-700 dark:text-neutral-300">
                        {projectInsights.executive_summary}
                      </p>
                    </div>

                    {/* Key Themes */}
                    {projectInsights.key_themes.length > 0 && (
                      <div>
                        <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                          <Layers className="h-5 w-5 text-blue-500" />
                          Główne tematy
                        </h3>
                        <div className="flex flex-wrap gap-2">
                          {projectInsights.key_themes.map((theme, i) => (
                            <Badge key={i} variant="secondary" className="px-3 py-1">
                              {theme}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Top Categories */}
                    {projectInsights.top_categories.length > 0 && (
                      <div>
                        <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                          <FolderTree className="h-5 w-5 text-green-500" />
                          Top kategorie
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                          {projectInsights.top_categories.map((cat, i) => (
                            <Card key={i} className="p-3">
                              <p className="font-medium">{cat.name}</p>
                              <p className="text-sm text-neutral-500">
                                {cat.documents} dokumentów
                              </p>
                            </Card>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Patterns */}
                    {projectInsights.patterns.length > 0 && (
                      <div>
                        <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                          <TrendingUp className="h-5 w-5 text-orange-500" />
                          Wykryte wzorce
                        </h3>
                        <ul className="space-y-2">
                          {projectInsights.patterns.map((pattern, i) => (
                            <li key={i} className="flex items-start gap-2">
                              <CheckCircle2 className="h-5 w-5 text-success-500 flex-shrink-0 mt-0.5" />
                              <span className="text-neutral-700 dark:text-neutral-300">
                                {pattern}
                              </span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Recommendations */}
                    {projectInsights.recommendations.length > 0 && (
                      <div>
                        <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                          <Lightbulb className="h-5 w-5 text-yellow-500" />
                          Rekomendacje
                        </h3>
                        <ul className="space-y-2">
                          {projectInsights.recommendations.map((rec, i) => (
                            <li key={i} className="flex items-start gap-2">
                              <ArrowRight className="h-5 w-5 text-primary-500 flex-shrink-0 mt-0.5" />
                              <span className="text-neutral-700 dark:text-neutral-300">
                                {rec}
                              </span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Document Summaries */}
                    {projectInsights.document_summaries.length > 0 && (
                      <div>
                        <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                          <FileText className="h-5 w-5 text-indigo-500" />
                          Analizowane dokumenty ({projectInsights.total_documents})
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {projectInsights.document_summaries.map((doc) => (
                            <Card key={doc.document_id} className="p-4">
                              <div className="flex items-start justify-between mb-2">
                                <h4 className="font-medium line-clamp-1">{doc.title}</h4>
                                <Badge
                                  className={getSentimentColor(doc.sentiment)}
                                  variant="secondary"
                                >
                                  {getSentimentLabel(doc.sentiment)}
                                </Badge>
                              </div>
                              <p className="text-sm text-neutral-600 dark:text-neutral-400 line-clamp-2 mb-2">
                                {doc.summary}
                              </p>
                              <div className="flex items-center justify-between text-xs text-neutral-500">
                                <span>Ważność: {(doc.importance_score * 100).toFixed(0)}%</span>
                                <Progress value={doc.importance_score * 100} className="w-20 h-2" />
                              </div>
                            </Card>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Generated at */}
                    <p className="text-xs text-neutral-500 text-center">
                      Wygenerowano: {new Date(projectInsights.generated_at).toLocaleString('pl-PL')}
                    </p>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Document Insights Tab */}
        <TabsContent value="document" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Generuj wnioski z dokumentu</CardTitle>
              <CardDescription>
                Analizuje pojedynczy dokument pod kątem kluczowych odkryć, tematów i akcji
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Document ID input */}
              <div>
                <label className="text-sm font-medium mb-2 block">
                  ID dokumentu
                </label>
                <div className="flex gap-2">
                  <input
                    type="number"
                    placeholder="np. 123"
                    value={selectedDocumentId || ''}
                    onChange={(e) => setSelectedDocumentId(Number(e.target.value))}
                    disabled={generatingDocument}
                    className="flex-1 px-3 py-2 rounded-md border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-900"
                  />
                  <Button
                    onClick={handleGenerateDocumentInsights}
                    disabled={generatingDocument || !selectedDocumentId}
                  >
                    {generatingDocument ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Generowanie...
                      </>
                    ) : (
                      <>
                        <Sparkles className="h-4 w-4 mr-2" />
                        Generuj
                      </>
                    )}
                  </Button>
                </div>
                <p className="text-xs text-neutral-500 mt-1">
                  Znajdź ID dokumentu na stronie{' '}
                  <button
                    onClick={() => selectedProject && navigate(`/projects/${selectedProject}/documents`)}
                    className="underline hover:text-primary-500"
                  >
                    Dokumenty
                  </button>
                </p>
              </div>

              {/* Document Insights Results */}
              {documentInsights && (
                <>
                  <Separator />
                  <div className="space-y-4">
                    {/* Title and sentiment */}
                    <div className="flex items-start justify-between">
                      <h3 className="text-lg font-semibold">{documentInsights.title}</h3>
                      <Badge className={getSentimentColor(documentInsights.sentiment)}>
                        {getSentimentLabel(documentInsights.sentiment)}
                      </Badge>
                    </div>

                    {/* Summary */}
                    <div>
                      <h4 className="font-medium mb-2">Podsumowanie</h4>
                      <p className="text-neutral-700 dark:text-neutral-300">
                        {documentInsights.summary}
                      </p>
                    </div>

                    {/* Key Findings */}
                    {documentInsights.key_findings.length > 0 && (
                      <div>
                        <h4 className="font-medium mb-2">Kluczowe odkrycia</h4>
                        <ul className="space-y-1">
                          {documentInsights.key_findings.map((finding, i) => (
                            <li key={i} className="flex items-start gap-2 text-sm">
                              <CheckCircle2 className="h-4 w-4 text-success-500 flex-shrink-0 mt-0.5" />
                              <span>{finding}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Topics */}
                    {documentInsights.topics.length > 0 && (
                      <div>
                        <h4 className="font-medium mb-2">Tematy</h4>
                        <div className="flex flex-wrap gap-2">
                          {documentInsights.topics.map((topic, i) => (
                            <Badge key={i} variant="outline">
                              {topic}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Entities */}
                    {documentInsights.entities.length > 0 && (
                      <div>
                        <h4 className="font-medium mb-2">Encje</h4>
                        <div className="flex flex-wrap gap-2">
                          {documentInsights.entities.map((entity, i) => (
                            <Badge key={i} variant="secondary">
                              {entity}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Action Items */}
                    {documentInsights.action_items.length > 0 && (
                      <div>
                        <h4 className="font-medium mb-2">Elementy akcji</h4>
                        <ul className="space-y-1">
                          {documentInsights.action_items.map((action, i) => (
                            <li key={i} className="flex items-start gap-2 text-sm">
                              <Target className="h-4 w-4 text-primary-500 flex-shrink-0 mt-0.5" />
                              <span>{action}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Importance Score */}
                    <div>
                      <h4 className="font-medium mb-2">Ważność dokumentu</h4>
                      <div className="flex items-center gap-3">
                        <Progress value={documentInsights.importance_score * 100} className="flex-1" />
                        <span className="text-sm font-medium">
                          {(documentInsights.importance_score * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Info card */}
      <Card className="bg-purple-50 dark:bg-purple-950 border-purple-200 dark:border-purple-800 mt-6">
        <CardContent className="pt-6">
          <div className="flex gap-3">
            <Sparkles className="h-5 w-5 text-purple-600 dark:text-purple-400 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-purple-800 dark:text-purple-200">
              <p className="font-medium mb-1">AI Insights</p>
              <p className="text-xs opacity-90">
                Funkcja używa Claude AI do analizy dokumentów i generowania
                strukturyzowanych wniosków. Wymaga skonfigurowanego klucza
                ANTHROPIC_API_KEY.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
