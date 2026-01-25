/**
 * KnowledgeTree - Web Crawling Page
 * Single URL and batch crawling with Firecrawl integration
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Globe,
  Play,
  Loader2,
  CheckCircle2,
  XCircle,
  FileText,
  FolderTree,
  AlertCircle,
  Copy,
  RefreshCw,
  Layers,
  Clock,
  ExternalLink,
} from 'lucide-react';
import { crawlApi, projectsApi, categoriesApi } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Checkbox } from '@/components/ui/checkbox';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';

interface Project {
  id: number;
  name: string;
  description?: string;
  color?: string;
  documents_count?: number;
}

interface Category {
  id: number;
  name: string;
  description?: string;
  color?: string;
  depth?: number;
  parent_id?: number | null;
}

interface CrawlResult {
  success: boolean;
  url: string;
  title: string;
  engine: string;
  text_length: number;
  links_count: number;
  images_count: number;
  status_code: number;
  error?: string;
  preview?: string;
}

interface BatchJob {
  job_id: number;
  project_id: number;
  status: 'pending' | 'processing' | 'completed' | 'partial' | 'failed';
  total_urls: number;
  completed_urls: number;
  failed_urls: number;
  created_at: string;
  updated_at: string;
  error?: string;
}

export default function CrawlPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { toast } = useToast();

  // State
  const [projects, setProjects] = useState<Project[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedProject, setSelectedProject] = useState<number | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  // Single URL crawl
  const [singleUrl, setSingleUrl] = useState('');
  const [singleEngine, setSingleEngine] = useState<'auto' | 'http' | 'playwright' | 'firecrawl'>('auto');
  const [singleCrawling, setSingleCrawling] = useState(false);
  const [singleResult, setSingleResult] = useState<CrawlResult | null>(null);

  // Batch crawl
  const [batchUrls, setBatchUrls] = useState('');
  const [batchEngine, setBatchEngine] = useState<'auto' | 'http' | 'playwright' | 'firecrawl'>('auto');
  const [batchConcurrency, setBatchConcurrency] = useState(5);
  const [batchJob, setBatchJob] = useState<BatchJob | null>(null);
  const [batchCrawling, setBatchCrawling] = useState(false);

  // Options
  const [extractLinks, setExtractLinks] = useState(true);
  const [extractImages, setExtractImages] = useState(false);
  const [saveToDb, setSaveToDb] = useState(true);

  // Load projects on mount
  useEffect(() => {
    loadProjects();
  }, []);

  // Load categories when project selected
  useEffect(() => {
    if (selectedProject) {
      loadCategories();
    }
  }, [selectedProject]);

  // Poll batch job status
  useEffect(() => {
    if (batchJob && (batchJob.status === 'pending' || batchJob.status === 'processing')) {
      const interval = setInterval(() => {
        pollBatchJob(batchJob.job_id);
      }, 2000);
      return () => clearInterval(interval);
    }
  }, [batchJob]);

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

  const loadCategories = async () => {
    if (!selectedProject) return;

    try {
      const response = await categoriesApi.getTree(selectedProject, null, 3);
      setCategories(response.data.categories || []);
    } catch (error) {
      console.error('Failed to load categories:', error);
    }
  };

  const pollBatchJob = async (jobId: number) => {
    try {
      const response = await crawlApi.getJob(jobId);
      setBatchJob(response.data);
    } catch (error) {
      console.error('Failed to poll job status:', error);
    }
  };

  const handleSingleCrawl = async () => {
    if (!singleUrl) {
      toast({
        title: 'Błąd',
        description: 'Wprowadź URL do crawlowania',
        variant: 'destructive',
      });
      return;
    }

    setSingleCrawling(true);
    setSingleResult(null);

    try {
      const engine = singleEngine === 'auto' ? undefined : singleEngine;
      const response = await crawlApi.single({
        url: singleUrl,
        engine,
        extract_links: extractLinks,
        extract_images: extractImages,
        save_to_db: saveToDb && selectedProject ? true : false,
        category_id: selectedCategory,
      });

      setSingleResult(response.data);

      if (response.data.success) {
        toast({
          title: 'Sukces',
          description: `Pobrano "${response.data.title}" (${response.data.text_length} znaków)`,
        });
      } else {
        toast({
          title: 'Ostrzeżenie',
          description: response.data.error || 'Nie udało się pobrać strony',
          variant: 'destructive',
        });
      }
    } catch (error: any) {
      toast({
        title: 'Błąd',
        description: error.response?.data?.detail || 'Nie udało się przeprowadzić crawlowania',
        variant: 'destructive',
      });
    } finally {
      setSingleCrawling(false);
    }
  };

  const handleBatchCrawl = async () => {
    if (!selectedProject) {
      toast({
        title: 'Błąd',
        description: 'Wybierz projekt do którego zapisać wyniki',
        variant: 'destructive',
      });
      return;
    }

    // Parse URLs from textarea
    const urls = batchUrls
      .split('\n')
      .map(url => url.trim())
      .filter(url => url.length > 0);

    if (urls.length === 0) {
      toast({
        title: 'Błąd',
        description: 'Wprowadź przynajmniej jeden URL',
        variant: 'destructive',
      });
      return;
    }

    if (urls.length > 50) {
      toast({
        title: 'Błąd',
        description: 'Maksymalnie 50 URLi jednocześnie',
        variant: 'destructive',
      });
      return;
    }

    setBatchCrawling(true);
    setBatchJob(null);

    try {
      const engine = batchEngine === 'auto' ? undefined : batchEngine;
      const response = await crawlApi.batch({
        urls,
        engine,
        extract_links: extractLinks,
        extract_images: extractImages,
        category_id: selectedCategory,
        concurrency: batchConcurrency,
      });

      setBatchJob(response.data);
      toast({
        title: 'Uruchomiono',
        description: `Job ID: ${response.data.job_id} - ${response.data.total_urls} URLi do przetworzenia`,
      });
    } catch (error: any) {
      toast({
        title: 'Błąd',
        description: error.response?.data?.detail || 'Nie udało się uruchomić crawlowania',
        variant: 'destructive',
      });
      setBatchCrawling(false);
    }
  };

  const getJobProgress = () => {
    if (!batchJob) return 0;
    return (batchJob.completed_urls + batchJob.failed_urls) / batchJob.total_urls * 100;
  };

  const getJobStatusBadge = () => {
    if (!batchJob) return null;

    const statusMap = {
      pending: { label: 'Oczekujący', color: 'bg-neutral-500' },
      processing: { label: 'Przetwarzanie', color: 'bg-blue-500' },
      completed: { label: 'Ukończono', color: 'bg-success-500' },
      partial: { label: 'Częściowo', color: 'bg-warning-500' },
      failed: { label: 'Błąd', color: 'bg-error-500' },
    };

    const status = statusMap[batchJob.status as keyof typeof statusMap];
    return (
      <Badge className={status.color}>
        {status.label}
      </Badge>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-primary-500" />
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4 max-w-6xl">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 bg-primary-100 dark:bg-primary-900/30 rounded-lg">
            <Globe className="h-6 w-6 text-primary-600 dark:text-primary-400" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-neutral-900 dark:text-neutral-50">
              {t('crawl.title')}
            </h1>
            <p className="text-neutral-600 dark:text-neutral-400">
              {t('crawl.description')}
            </p>
          </div>
        </div>
      </div>

      {/* Configuration */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Layers className="h-5 w-5" />
            Konfiguracja
          </CardTitle>
          <CardDescription>
            Wybierz projekt i kategorię dla pobranych treści
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Project selector */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="project" className="flex items-center gap-2">
                <FolderTree className="h-4 w-4" />
                Projekt
              </Label>
              <Select
                value={selectedProject?.toString() || ''}
                onValueChange={(value) => setSelectedProject(Number(value))}
              >
                <SelectTrigger id="project">
                  <SelectValue placeholder="Wybierz projekt" />
                </SelectTrigger>
                <SelectContent>
                  {projects.map((project) => (
                    <SelectItem key={project.id} value={project.id.toString()}>
                      <div className="flex items-center gap-2">
                        {project.color && (
                          <div
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: project.color }}
                          />
                        )}
                        <span>{project.name}</span>
                        {project.documents_count !== undefined && (
                          <Badge variant="secondary" className="ml-auto">
                            {project.documents_count}
                          </Badge>
                        )}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Category selector */}
            <div>
              <Label htmlFor="category" className="flex items-center gap-2">
                <FileText className="h-4 w-4" />
                Kategoria (opcjonalne)
              </Label>
              <Select
                value={selectedCategory?.toString() || ''}
                onValueChange={(value) => setSelectedCategory(value ? Number(value) : null)}
              >
                <SelectTrigger id="category">
                  <SelectValue placeholder="Bez kategorii" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Bez kategorii</SelectItem>
                  {categories.map((category) => (
                    <SelectItem key={category.id} value={category.id.toString()}>
                      <div className="flex items-center gap-2">
                        {'  '.repeat(category.depth || 0)}
                        {category.color && (
                          <div
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: category.color }}
                          />
                        )}
                        <span>{category.name}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Options */}
          <div className="flex flex-wrap gap-6">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="extractLinks"
                checked={extractLinks}
                onCheckedChange={(checked) => setExtractLinks(checked === true)}
              />
              <Label htmlFor="extractLinks" className="cursor-pointer">
                Eksktrahuj linki
              </Label>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="extractImages"
                checked={extractImages}
                onCheckedChange={(checked) => setExtractImages(checked === true)}
              />
              <Label htmlFor="extractImages" className="cursor-pointer">
                Eksktrahuj obrazy
              </Label>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="saveToDb"
                checked={saveToDb}
                onCheckedChange={(checked) => setSaveToDb(checked === true)}
              />
              <Label htmlFor="saveToDb" className="cursor-pointer">
                Zapisz do bazy
              </Label>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main content tabs */}
      <Tabs defaultValue="single" className="space-y-6">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="single">Pojedynczy URL</TabsTrigger>
          <TabsTrigger value="batch">Batch Crawling</TabsTrigger>
        </TabsList>

        {/* Single URL Tab */}
        <TabsContent value="single" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Pobranie pojedynczej strony</CardTitle>
              <CardDescription>
                Wprowadź URL strony do pobrania. System automatycznie wybierze odpowiednią silnik.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* URL Input */}
              <div>
                <Label htmlFor="url" className="flex items-center gap-2">
                  <Globe className="h-4 w-4" />
                  URL
                </Label>
                <div className="flex gap-2 mt-1.5">
                  <Input
                    id="url"
                    type="url"
                    placeholder="https://example.com"
                    value={singleUrl}
                    onChange={(e) => setSingleUrl(e.target.value)}
                    disabled={singleCrawling}
                  />
                  <Button
                    onClick={handleSingleCrawl}
                    disabled={singleCrawling || !singleUrl}
                    className="min-w-32"
                  >
                    {singleCrawling ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Pobieranie...
                      </>
                    ) : (
                      <>
                        <Play className="h-4 w-4 mr-2" />
                        Pobierz
                      </>
                    )}
                  </Button>
                </div>
              </div>

              {/* Engine Selection */}
              <div>
                <Label htmlFor="engine">Silnik (opcjonalne)</Label>
                <Select
                  value={singleEngine}
                  onValueChange={(value: any) => setSingleEngine(value)}
                  disabled={singleCrawling}
                >
                  <SelectTrigger id="engine" className="mt-1.5">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="auto">
                      <div className="flex flex-col">
                        <span className="font-medium">Auto</span>
                        <span className="text-sm text-neutral-500">
                          Automatyczny wybór (zalecane)
                        </span>
                      </div>
                    </SelectItem>
                    <SelectItem value="http">
                      <div className="flex flex-col">
                        <span className="font-medium">HTTP</span>
                        <span className="text-sm text-neutral-500">
                          Szybki scraper dla statycznych stron (80% stron)
                        </span>
                      </div>
                    </SelectItem>
                    <SelectItem value="playwright">
                      <div className="flex flex-col">
                        <span className="font-medium">Playwright</span>
                        <span className="text-sm text-neutral-500">
                          Przeglądarka dla JS-heavy stron (15% stron)
                        </span>
                      </div>
                    </SelectItem>
                    <SelectItem value="firecrawl">
                      <div className="flex flex-col">
                        <span className="font-medium">Firecrawl</span>
                        <span className="text-sm text-neutral-500">
                          API dla trudnych stron z anti-bot (5% stron)
                        </span>
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Results */}
              {singleResult && (
                <>
                  <Separator />
                  <div className="space-y-4">
                    {/* Success/Error Alert */}
                    <Alert className={singleResult.success ? 'border-success-500' : 'border-error-500'}>
                      {singleResult.success ? (
                        <CheckCircle2 className="h-4 w-4 text-success-500" />
                      ) : (
                        <XCircle className="h-4 w-4 text-error-500" />
                      )}
                      <AlertDescription>
                        <div className="flex flex-col gap-2">
                          <span className="font-medium">
                            {singleResult.success ? 'Sukces' : 'Błąd'}
                          </span>
                          {singleResult.error && (
                            <span className="text-sm">{singleResult.error}</span>
                          )}
                        </div>
                      </AlertDescription>
                    </Alert>

                    {/* Result details */}
                    {singleResult.success && (
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div>
                          <Label className="text-neutral-500 text-sm">Tytuł</Label>
                          <p className="font-medium truncate">{singleResult.title || '-'}</p>
                        </div>
                        <div>
                          <Label className="text-neutral-500 text-sm">Silnik</Label>
                          <Badge variant="secondary">{singleResult.engine}</Badge>
                        </div>
                        <div>
                          <Label className="text-neutral-500 text-sm">Długość tekstu</Label>
                          <p className="font-medium">{singleResult.text_length.toLocaleString()} znaków</p>
                        </div>
                        <div>
                          <Label className="text-neutral-500 text-sm">Status</Label>
                          <Badge variant={singleResult.status_code === 200 ? 'default' : 'destructive'}>
                            {singleResult.status_code}
                          </Badge>
                        </div>
                      </div>
                    )}

                    {/* Preview */}
                    {singleResult.preview && (
                      <div>
                        <Label className="text-neutral-500 text-sm mb-2 block">Podgląd (pierwsze 500 znaków)</Label>
                        <div className="bg-neutral-100 dark:bg-neutral-800 rounded-lg p-4 max-h-64 overflow-y-auto">
                          <pre className="whitespace-pre-wrap text-sm font-sans">
                            {singleResult.preview}
                          </pre>
                        </div>
                      </div>
                    )}

                    {/* Actions */}
                    {singleResult.success && (
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            navigator.clipboard.writeText(singleResult.preview || '');
                            toast({ title: 'Skopiowano', description: 'Tekst skopiowany do schowka' });
                          }}
                        >
                          <Copy className="h-4 w-4 mr-2" />
                          Kopiuj tekst
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => window.open(singleUrl, '_blank')}
                        >
                          <ExternalLink className="h-4 w-4 mr-2" />
                          Otwórz URL
                        </Button>
                      </div>
                    )}
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Batch Tab */}
        <TabsContent value="batch" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Batch Crawling</CardTitle>
              <CardDescription>
                Wprowadź wiele URLi (jeden na linię) do przetworzenia w tle.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* URLs textarea */}
              <div>
                <Label htmlFor="urls" className="flex items-center gap-2">
                  <Globe className="h-4 w-4" />
                  Lista URLi (jeden na linię)
                </Label>
                <Textarea
                  id="urls"
                  placeholder="https://example.com/page1&#10;https://example.com/page2&#10;https://example.com/page3"
                  className="min-h-32 mt-1.5 font-mono text-sm"
                  value={batchUrls}
                  onChange={(e) => setBatchUrls(e.target.value)}
                  disabled={batchCrawling || (batchJob !== null && (batchJob.status === 'pending' || batchJob.status === 'processing'))}
                />
                <p className="text-sm text-neutral-500 mt-1.5">
                  {batchUrls.split('\n').filter(u => u.trim()).length} / 50 URLi
                </p>
              </div>

              {/* Engine and concurrency */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="batchEngine">Silnik</Label>
                  <Select
                    value={batchEngine}
                    onValueChange={(value: any) => setBatchEngine(value)}
                    disabled={batchCrawling || (batchJob !== null && (batchJob.status === 'pending' || batchJob.status === 'processing'))}
                  >
                    <SelectTrigger id="batchEngine" className="mt-1.5">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="auto">Auto (zalecane)</SelectItem>
                      <SelectItem value="http">HTTP (szybki)</SelectItem>
                      <SelectItem value="playwright">Playwright (JS)</SelectItem>
                      <SelectItem value="firecrawl">Firecrawl (trudne)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="concurrency">Równoległość: {batchConcurrency}</Label>
                  <input
                    id="concurrency"
                    type="range"
                    min="1"
                    max="10"
                    value={batchConcurrency}
                    onChange={(e) => setBatchConcurrency(Number(e.target.value))}
                    disabled={batchCrawling || (batchJob !== null && (batchJob.status === 'pending' || batchJob.status === 'processing'))}
                    className="w-full mt-1.5"
                  />
                </div>
              </div>

              {/* Start button */}
              <Button
                onClick={handleBatchCrawl}
                disabled={batchCrawling || (batchJob !== null && (batchJob.status === 'pending' || batchJob.status === 'processing')) || !batchUrls.trim()}
                className="w-full"
              >
                {batchCrawling ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Uruchamianie...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" />
                    Uruchom Batch Crawling
                  </>
                )}
              </Button>

              {/* Job status */}
              {batchJob && (
                <>
                  <Separator />
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {getJobStatusBadge()}
                        <div className="flex items-center gap-2 text-sm text-neutral-500">
                          <Clock className="h-4 w-4" />
                          <span>
                            {new Date(batchJob.created_at).toLocaleString('pl-PL')}
                          </span>
                        </div>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setBatchJob(null)}
                      >
                        <RefreshCw className="h-4 w-4 mr-2" />
                        Nowy batch
                      </Button>
                    </div>

                    {/* Progress bar */}
                    {batchJob.status === 'pending' || batchJob.status === 'processing' ? (
                      <div className="space-y-2">
                        <Progress value={getJobProgress()} />
                        <div className="flex justify-between text-sm text-neutral-500">
                          <span>
                            {batchJob.completed_urls + batchJob.failed_urls} / {batchJob.total_urls} ukończonych
                          </span>
                          <span>{Math.round(getJobProgress())}%</span>
                        </div>
                      </div>
                    ) : (
                      <div className="grid grid-cols-3 gap-4 text-center">
                        <div>
                          <p className="text-2xl font-bold text-success-500">
                            {batchJob.completed_urls}
                          </p>
                          <p className="text-sm text-neutral-500">Ukończone</p>
                        </div>
                        <div>
                          <p className="text-2xl font-bold text-error-500">
                            {batchJob.failed_urls}
                          </p>
                          <p className="text-sm text-neutral-500">Błędy</p>
                        </div>
                        <div>
                          <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
                            {batchJob.total_urls}
                          </p>
                          <p className="text-sm text-neutral-500">Razem</p>
                        </div>
                      </div>
                    )}

                    {/* Error */}
                    {batchJob.error && (
                      <Alert variant="destructive">
                        <AlertCircle className="h-4 w-4" />
                        <AlertDescription>{batchJob.error}</AlertDescription>
                      </Alert>
                    )}

                    {/* Navigate to documents */}
                    {(batchJob.status === 'completed' || batchJob.status === 'partial') && selectedProject && (
                      <Button
                        variant="outline"
                        onClick={() => navigate(`/projects/${selectedProject}/documents`)}
                      >
                        <FileText className="h-4 w-4 mr-2" />
                        Zobacz pobrane dokumenty
                      </Button>
                    )}
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Info card */}
      <Card className="bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800">
        <CardContent className="pt-6">
          <div className="flex gap-3">
            <AlertCircle className="h-5 w-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-blue-800 dark:text-blue-200 space-y-1">
              <p className="font-medium">Silniki crawlowania:</p>
              <ul className="list-disc list-inside space-y-1 text-xs">
                <li><strong>HTTP</strong> - Szybki dla statycznych stron HTML (~80% stron)</li>
                <li><strong>Playwright</strong> - Przeglądarka dla React/Vue/Angular (~15% stron)</li>
                <li><strong>Firecrawl</strong> - API dla stron z anti-bot, CAPTCHA (~5% stron)</li>
              </ul>
              <p className="text-xs mt-2">
                <strong>Firecrawl</strong> wymaga klucza API. Zarejestruj się na{' '}
                <a
                  href="https://www.firecrawl.dev"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="underline hover:text-blue-700 dark:hover:text-blue-300"
                >
                  firecrawl.dev
                </a>
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
