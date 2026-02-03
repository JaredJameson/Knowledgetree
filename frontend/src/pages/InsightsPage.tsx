/**
 * KnowledgeTree - AI Insights Page
 * AI-powered document and project insights
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import jsPDF from 'jspdf';
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
  Download,
  FileJson,
  BarChart3,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie,
  Legend,
} from 'recharts';
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
import { Skeleton } from '@/components/ui/skeleton';

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

  const exportToJSON = () => {
    if (!projectInsights) return;

    const dataStr = JSON.stringify(projectInsights, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `insights_${projectInsights.project_name}_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);

    toast({
      title: 'Sukces',
      description: 'Eksportowano wnioski do JSON',
    });
  };

  const exportToPDF = () => {
    if (!projectInsights) return;

    const doc = new jsPDF();
    const pageWidth = doc.internal.pageSize.getWidth();
    let yPos = 20;

    // Title
    doc.setFontSize(18);
    doc.text('AI Insights Report', pageWidth / 2, yPos, { align: 'center' });
    yPos += 10;

    doc.setFontSize(14);
    doc.text(projectInsights.project_name, pageWidth / 2, yPos, { align: 'center' });
    yPos += 10;

    doc.setFontSize(10);
    doc.text(new Date(projectInsights.generated_at).toLocaleString(), pageWidth / 2, yPos, { align: 'center' });
    yPos += 15;

    // Executive Summary
    doc.setFontSize(14);
    doc.text('Executive Summary', 20, yPos);
    yPos += 8;

    doc.setFontSize(10);
    const summaryLines = doc.splitTextToSize(projectInsights.executive_summary, pageWidth - 40);
    doc.text(summaryLines, 20, yPos);
    yPos += summaryLines.length * 6 + 10;

    // Key Themes
    if (projectInsights.key_themes.length > 0) {
      doc.setFontSize(12);
      doc.text('Key Themes', 20, yPos);
      yPos += 8;

      doc.setFontSize(10);
      projectInsights.key_themes.forEach((theme: string) => {
        doc.text(`• ${theme}`, 25, yPos);
        yPos += 6;
      });
      yPos += 5;
    }

    // Check if we need a new page
    if (yPos > 250) {
      doc.addPage();
      yPos = 20;
    }

    // Patterns
    if (projectInsights.patterns.length > 0) {
      doc.setFontSize(12);
      doc.text('Patterns', 20, yPos);
      yPos += 8;

      doc.setFontSize(10);
      projectInsights.patterns.forEach((pattern: string) => {
        const lines = doc.splitTextToSize(`• ${pattern}`, pageWidth - 45);
        doc.text(lines, 25, yPos);
        yPos += lines.length * 6;

        if (yPos > 270) {
          doc.addPage();
          yPos = 20;
        }
      });
      yPos += 5;
    }

    // Recommendations
    if (projectInsights.recommendations.length > 0) {
      if (yPos > 240) {
        doc.addPage();
        yPos = 20;
      }

      doc.setFontSize(12);
      doc.text('Recommendations', 20, yPos);
      yPos += 8;

      doc.setFontSize(10);
      projectInsights.recommendations.forEach((rec: string) => {
        const lines = doc.splitTextToSize(`• ${rec}`, pageWidth - 45);
        doc.text(lines, 25, yPos);
        yPos += lines.length * 6;

        if (yPos > 270) {
          doc.addPage();
          yPos = 20;
        }
      });
    }

    doc.save(`insights_${projectInsights.project_name}_${new Date().toISOString().split('T')[0]}.pdf`);

    toast({
      title: 'Sukces',
      description: 'Eksportowano wnioski do PDF',
    });
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
    <div className="container mx-auto py-4 sm:py-8 px-4 max-w-7xl">
      {/* Header */}
      <div className="mb-6 sm:mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
            <Brain className="h-5 w-5 sm:h-6 sm:w-6 text-purple-600 dark:text-purple-400" />
          </div>
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-neutral-900 dark:text-neutral-50">
              AI Insights
            </h1>
            <p className="text-sm sm:text-base text-neutral-600 dark:text-neutral-400">
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
          {loading ? (
            <div className="flex gap-2 flex-wrap">
              {[...Array(3)].map((_, i) => (
                <Skeleton key={i} className="h-9 w-32" />
              ))}
            </div>
          ) : (
            <div className="flex gap-2 flex-wrap">
              {projects.map((project) => (
                <Button
                  key={project.id}
                  variant={selectedProject === project.id ? 'default' : 'outline'}
                  onClick={() => setSelectedProject(project.id)}
                  className="text-sm sm:text-base"
                  size="sm"
                >
                  <FileText className="h-4 w-4 mr-1 sm:mr-2" />
                  <span className="truncate max-w-[150px] sm:max-w-none">{project.name}</span>
                  {project.documents_count !== undefined && (
                    <Badge variant="secondary" className="ml-1 sm:ml-2">
                      {project.documents_count}
                    </Badge>
                  )}
                </Button>
              ))}
            </div>
          )}
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

              {/* Loading State */}
              {generatingProject && (
                <>
                  <Separator />
                  <div className="space-y-6 pt-4">
                    {/* Executive Summary Skeleton */}
                    <div className="space-y-2">
                      <Skeleton className="h-6 w-48" />
                      <Skeleton className="h-4 w-full" />
                      <Skeleton className="h-4 w-full" />
                      <Skeleton className="h-4 w-3/4" />
                    </div>

                    {/* Key Themes Skeleton */}
                    <div className="space-y-2">
                      <Skeleton className="h-6 w-36" />
                      <div className="flex flex-wrap gap-2">
                        <Skeleton className="h-8 w-24" />
                        <Skeleton className="h-8 w-32" />
                        <Skeleton className="h-8 w-28" />
                        <Skeleton className="h-8 w-36" />
                      </div>
                    </div>

                    {/* Chart Skeleton */}
                    <div className="space-y-2">
                      <Skeleton className="h-6 w-32" />
                      <Skeleton className="h-[250px] w-full" />
                    </div>

                    {/* Patterns Skeleton */}
                    <div className="space-y-2">
                      <Skeleton className="h-6 w-40" />
                      <Skeleton className="h-4 w-full" />
                      <Skeleton className="h-4 w-5/6" />
                      <Skeleton className="h-4 w-4/6" />
                    </div>
                  </div>
                </>
              )}

              {/* Results */}
              {projectInsights && !generatingProject && (
                <>
                  <Separator />

                  {/* Export buttons */}
                  <div className="flex flex-col sm:flex-row justify-end gap-2 pt-4">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={exportToJSON}
                      className="flex items-center justify-center gap-2 w-full sm:w-auto"
                    >
                      <FileJson className="h-4 w-4" />
                      <span className="sm:inline">Eksportuj JSON</span>
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={exportToPDF}
                      className="flex items-center justify-center gap-2 w-full sm:w-auto"
                    >
                      <Download className="h-4 w-4" />
                      <span className="sm:inline">Eksportuj PDF</span>
                    </Button>
                  </div>

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
                        <div className="flex flex-wrap gap-3 items-center">
                          {projectInsights.key_themes.map((theme, i) => {
                            // Vary size based on order (first = most important)
                            const sizeClass = i === 0 ? 'text-lg px-4 py-2' :
                                            i === 1 ? 'text-base px-3 py-1.5' :
                                            'text-sm px-3 py-1';
                            const colorClass = i === 0 ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300' :
                                              i === 1 ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300' :
                                              'bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300';
                            return (
                              <Badge
                                key={i}
                                variant="secondary"
                                className={`${sizeClass} ${colorClass} font-medium`}
                              >
                                {theme}
                              </Badge>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* Top Categories */}
                    {projectInsights.top_categories.length > 0 && (
                      <div>
                        <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                          <BarChart3 className="h-5 w-5 text-green-500" />
                          Top kategorie
                        </h3>
                        <Card className="p-2 sm:p-4">
                          <ResponsiveContainer width="100%" height={250} className="sm:h-[300px]">
                            <BarChart
                              data={projectInsights.top_categories}
                              margin={{ top: 10, right: 10, left: 0, bottom: 60 }}
                            >
                              <CartesianGrid strokeDasharray="3 3" className="stroke-neutral-200 dark:stroke-neutral-700" />
                              <XAxis
                                dataKey="name"
                                angle={-45}
                                textAnchor="end"
                                height={80}
                                className="text-xs fill-neutral-600 dark:fill-neutral-400"
                              />
                              <YAxis className="text-xs fill-neutral-600 dark:fill-neutral-400" />
                              <Tooltip
                                contentStyle={{
                                  backgroundColor: 'var(--background)',
                                  border: '1px solid var(--border)',
                                  borderRadius: '6px',
                                }}
                                labelStyle={{ color: 'var(--foreground)' }}
                              />
                              <Bar dataKey="documents" name="Dokumenty" radius={[8, 8, 0, 0]}>
                                {projectInsights.top_categories.map((entry, index) => (
                                  <Cell
                                    key={`cell-${index}`}
                                    fill={`hsl(${(index * 360) / projectInsights.top_categories.length}, 70%, 50%)`}
                                  />
                                ))}
                              </Bar>
                            </BarChart>
                          </ResponsiveContainer>
                        </Card>
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

                    {/* Sentiment Distribution */}
                    {projectInsights.document_summaries.length > 0 && (() => {
                      const sentimentCounts = projectInsights.document_summaries.reduce((acc, doc) => {
                        acc[doc.sentiment] = (acc[doc.sentiment] || 0) + 1;
                        return acc;
                      }, {} as Record<string, number>);

                      const sentimentData = Object.entries(sentimentCounts).map(([sentiment, count]) => ({
                        name: getSentimentLabel(sentiment),
                        value: count,
                        color: sentiment === 'positive' ? '#10b981' : sentiment === 'negative' ? '#ef4444' : '#6b7280',
                      }));

                      return sentimentData.length > 0 ? (
                        <div>
                          <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                            <Target className="h-5 w-5 text-purple-500" />
                            Analiza sentymentu dokumentów
                          </h3>
                          <Card className="p-2 sm:p-4">
                            <ResponsiveContainer width="100%" height={250} className="sm:h-[300px]">
                              <PieChart>
                                <Pie
                                  data={sentimentData}
                                  cx="50%"
                                  cy="50%"
                                  labelLine={false}
                                  label={(entry) => `${entry.name}: ${entry.value}`}
                                  outerRadius={100}
                                  fill="#8884d8"
                                  dataKey="value"
                                >
                                  {sentimentData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.color} />
                                  ))}
                                </Pie>
                                <Tooltip
                                  contentStyle={{
                                    backgroundColor: 'var(--background)',
                                    border: '1px solid var(--border)',
                                    borderRadius: '6px',
                                  }}
                                />
                                <Legend />
                              </PieChart>
                            </ResponsiveContainer>
                          </Card>
                        </div>
                      ) : null;
                    })()}

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
                <div className="flex flex-col sm:flex-row gap-2">
                  <input
                    type="number"
                    placeholder="np. 123"
                    value={selectedDocumentId || ''}
                    onChange={(e) => setSelectedDocumentId(Number(e.target.value))}
                    disabled={generatingDocument}
                    className="flex-1 px-3 py-2 rounded-md border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-900 text-sm sm:text-base"
                  />
                  <Button
                    onClick={handleGenerateDocumentInsights}
                    disabled={generatingDocument || !selectedDocumentId}
                    className="w-full sm:w-auto"
                    size="default"
                  >
                    {generatingDocument ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        <span className="text-sm sm:text-base">Generowanie...</span>
                      </>
                    ) : (
                      <>
                        <Sparkles className="h-4 w-4 mr-2" />
                        <span className="text-sm sm:text-base">Generuj</span>
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

              {/* Document Loading State */}
              {generatingDocument && (
                <>
                  <Separator />
                  <div className="space-y-4 pt-4">
                    {/* Title Skeleton */}
                    <div className="flex items-start justify-between">
                      <Skeleton className="h-6 w-48" />
                      <Skeleton className="h-6 w-20" />
                    </div>

                    {/* Summary Skeleton */}
                    <div className="space-y-2">
                      <Skeleton className="h-5 w-32" />
                      <Skeleton className="h-4 w-full" />
                      <Skeleton className="h-4 w-full" />
                      <Skeleton className="h-4 w-3/4" />
                    </div>

                    {/* Key Findings Skeleton */}
                    <div className="space-y-2">
                      <Skeleton className="h-5 w-36" />
                      <Skeleton className="h-4 w-full" />
                      <Skeleton className="h-4 w-5/6" />
                      <Skeleton className="h-4 w-4/6" />
                    </div>

                    {/* Topics Skeleton */}
                    <div className="space-y-2">
                      <Skeleton className="h-5 w-24" />
                      <div className="flex flex-wrap gap-2">
                        <Skeleton className="h-6 w-20" />
                        <Skeleton className="h-6 w-24" />
                        <Skeleton className="h-6 w-28" />
                      </div>
                    </div>
                  </div>
                </>
              )}

              {/* Document Insights Results */}
              {documentInsights && !generatingDocument && (
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
