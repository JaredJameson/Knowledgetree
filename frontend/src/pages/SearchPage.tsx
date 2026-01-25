/**
 * KnowledgeTree Search Page
 * Semantic search across document knowledge base
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/context/AuthContext';
import { projectsApi, searchApi, exportApi, categoriesApi, type SearchResultExport } from '@/lib/api';
import { downloadBlob } from '@/lib/download';
import type { Project, SearchResult } from '@/types/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { LanguageSwitcher } from '@/components/language-switcher';
import { ThemeToggle } from '@/components/theme-toggle';
import {
  Loader2,
  Search,
  FileText,
  ChevronLeft,
  ExternalLink,
  TrendingUp,
  Database,
  Layers,
  Download
} from 'lucide-react';

export function SearchPage() {
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  // Projects state
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [loadingProjects, setLoadingProjects] = useState(true);

  // Categories state
  const [categories, setCategories] = useState<any[]>([]);
  const [loadingCategories, setLoadingCategories] = useState(false);

  // Search state
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [searchTime, setSearchTime] = useState<number>(0);
  const [error, setError] = useState('');

  // Filters
  const [minSimilarity, setMinSimilarity] = useState(0.5);
  const [maxResults, setMaxResults] = useState(10);
  const [selectedCategoryId, setSelectedCategoryId] = useState<number | null>(null);

  // Statistics
  const [stats, setStats] = useState<any>(null);
  const [loadingStats, setLoadingStats] = useState(false);

  // Load projects on mount
  useEffect(() => {
    loadProjects();
  }, []);

  // Load statistics when project changes
  useEffect(() => {
    if (selectedProjectId) {
      loadStatistics();
    } else {
      setStats(null);
    }
  }, [selectedProjectId]);

  // Load categories when project changes
  useEffect(() => {
    if (selectedProjectId) {
      loadCategories();
    } else {
      setCategories([]);
      setSelectedCategoryId(null);
    }
  }, [selectedProjectId]);

  const loadProjects = async () => {
    try {
      setLoadingProjects(true);
      const response = await projectsApi.list();
      const projectsData = response.data.projects || response.data || [];
      setProjects(projectsData);

      // Auto-select first project if available
      if (projectsData.length > 0 && !selectedProjectId) {
        setSelectedProjectId(projectsData[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load projects');
    } finally {
      setLoadingProjects(false);
    }
  };

  const loadStatistics = async () => {
    if (!selectedProjectId) return;

    try {
      setLoadingStats(true);
      const response = await searchApi.statistics(selectedProjectId);
      setStats(response.data);
    } catch (err) {
      console.error('Failed to load statistics:', err);
    } finally {
      setLoadingStats(false);
    }
  };

  const loadCategories = async () => {
    if (!selectedProjectId) return;

    try {
      setLoadingCategories(true);
      // Load categories as a flat list for the dropdown
      const response = await categoriesApi.list(selectedProjectId, null, 1, 1000);
      setCategories(response.data || []);
    } catch (err) {
      console.error('Failed to load categories:', err);
    } finally {
      setLoadingCategories(false);
    }
  };

  const handleSearch = async (e?: React.FormEvent) => {
    e?.preventDefault();

    if (!query.trim()) {
      setError(t('search.errors.noQuery'));
      return;
    }

    if (!selectedProjectId) {
      setError(t('search.errors.noProject'));
      return;
    }

    try {
      setSearching(true);
      setError('');
      setResults([]);

      const response = await searchApi.search({
        query: query.trim(),
        project_id: selectedProjectId || undefined,
        category_id: selectedCategoryId || undefined,
        limit: maxResults,
        min_similarity: minSimilarity,
      });

      setResults(response.data.results);
      setSearchTime(response.data.search_time);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('search.errors.searchFailed'));
    } finally {
      setSearching(false);
    }
  };

  const getSimilarityBadge = (score: number) => {
    if (score >= 0.8) return 'default';
    if (score >= 0.6) return 'secondary';
    return 'outline';
  };

  // Export search results as CSV
  const handleExportResults = async () => {
    if (results.length === 0) return;

    try {
      // Convert SearchResult to SearchResultExport format
      const exportData: SearchResultExport[] = results.map((result) => ({
        document_title: result.document_title || 'Untitled',
        chunk_index: result.chunk_index,
        page_number: result.chunk_metadata?.page_number,
        similarity_score: result.similarity_score,
        chunk_text: result.chunk_text,
      }));

      const response = await exportApi.exportSearchResultsCSV(exportData);
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
      const filename = `search_results_${timestamp}.csv`;
      downloadBlob(response.data, filename);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to export search results');
    }
  };

  const selectedProject = projects.find(p => p.id === selectedProjectId);

  return (
    <div className="min-h-screen bg-neutral-50 dark:bg-neutral-900">
      {/* Header */}
      <header className="border-b border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-950">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/dashboard')}
              >
                <ChevronLeft className="h-4 w-4 mr-1" />
                Dashboard
              </Button>
              <div className="h-8 w-px bg-neutral-200 dark:bg-neutral-800" />
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
          {/* Header with Project Selector */}
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-3xl font-bold text-neutral-900 dark:text-neutral-50">
                {t('search.title')}
              </h2>
              <p className="text-neutral-600 dark:text-neutral-400 mt-2">
                {selectedProject?.name || t('search.description')}
              </p>
            </div>

            {/* Project Selector */}
            <div className="w-64">
              <Select
                value={selectedProjectId?.toString()}
                onValueChange={(value: string) => setSelectedProjectId(parseInt(value))}
                disabled={loadingProjects}
              >
                <SelectTrigger>
                  <SelectValue placeholder={t('search.selectProject')} />
                </SelectTrigger>
                <SelectContent>
                  {projects.map((project) => (
                    <SelectItem key={project.id} value={project.id.toString()}>
                      {project.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="p-4 bg-error-50 dark:bg-error-900/20 border border-error-200 dark:border-error-800 rounded text-error-700 dark:text-error-400">
              {error}
            </div>
          )}

          {/* No Project Selected */}
          {!selectedProjectId && !loadingProjects && (
            <Card className="text-center py-12">
              <CardContent>
                <Search className="mx-auto h-12 w-12 text-neutral-400 mb-4" />
                <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-50 mb-2">
                  {t('search.noProjectSelected')}
                </h3>
                <p className="text-neutral-600 dark:text-neutral-400 mb-4">
                  {t('search.noProjectSelectedDescription')}
                </p>
                <Button onClick={() => navigate('/projects')}>
                  {t('documents.backToProjects')}
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Search Interface */}
          {selectedProjectId && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Left Column - Search & Filters */}
              <div className="space-y-6">
                {/* Search Box */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Search className="h-5 w-5" />
                      {t('search.title')}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <form onSubmit={handleSearch} className="space-y-4">
                      <div className="space-y-2">
                        <Input
                          value={query}
                          onChange={(e) => setQuery(e.target.value)}
                          placeholder={t('search.searchPlaceholder')}
                          disabled={searching}
                        />
                      </div>
                      <Button
                        type="submit"
                        className="w-full"
                        disabled={searching || !query.trim()}
                      >
                        {searching ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            {t('search.searching')}
                          </>
                        ) : (
                          <>
                            <Search className="mr-2 h-4 w-4" />
                            {t('search.searchButton')}
                          </>
                        )}
                      </Button>
                    </form>
                  </CardContent>
                </Card>

                {/* Filters */}
                <Card>
                  <CardHeader>
                    <CardTitle>{t('search.filters.title')}</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="min-similarity">
                        {t('search.filters.minSimilarity')}
                      </Label>
                      <div className="flex items-center gap-2">
                        <Input
                          id="min-similarity"
                          type="number"
                          min="0"
                          max="1"
                          step="0.1"
                          value={minSimilarity}
                          onChange={(e) => setMinSimilarity(parseFloat(e.target.value))}
                          className="flex-1"
                        />
                        <span className="text-sm text-neutral-600 dark:text-neutral-400 w-12">
                          {(minSimilarity * 100).toFixed(0)}%
                        </span>
                      </div>
                      <p className="text-xs text-neutral-500 dark:text-neutral-600">
                        {t('search.filters.minSimilarityDescription')}
                      </p>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="max-results">
                        {t('search.filters.maxResults')}
                      </Label>
                      <Input
                        id="max-results"
                        type="number"
                        min="1"
                        max="50"
                        value={maxResults}
                        onChange={(e) => setMaxResults(parseInt(e.target.value))}
                      />
                      <p className="text-xs text-neutral-500 dark:text-neutral-600">
                        {t('search.filters.maxResultsDescription')}
                      </p>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="category-filter">
                        {t('search.filters.category', 'Category')}
                      </Label>
                      <Select
                        value={selectedCategoryId?.toString() || 'all'}
                        onValueChange={(value) => setSelectedCategoryId(value === 'all' ? null : parseInt(value))}
                        disabled={loadingCategories || categories.length === 0}
                      >
                        <SelectTrigger id="category-filter">
                          <SelectValue placeholder={t('search.filters.allCategories', 'All Categories')} />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">
                            {t('search.filters.allCategories', 'All Categories')}
                          </SelectItem>
                          {categories.map((category) => (
                            <SelectItem key={category.id} value={category.id.toString()}>
                              <div className="flex items-center gap-2">
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
                      <p className="text-xs text-neutral-500 dark:text-neutral-600">
                        {t('search.filters.categoryDescription', 'Filter search by document category')}
                      </p>
                    </div>
                  </CardContent>
                </Card>

                {/* Statistics */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <TrendingUp className="h-5 w-5" />
                      {t('search.stats.title')}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {loadingStats ? (
                      <div className="flex items-center justify-center py-4">
                        <Loader2 className="h-6 w-6 animate-spin text-primary-600" />
                      </div>
                    ) : stats ? (
                      <div className="space-y-3">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-neutral-600 dark:text-neutral-400 flex items-center">
                            <FileText className="mr-2 h-4 w-4" />
                            {t('search.stats.totalDocuments')}
                          </span>
                          <span className="font-medium text-neutral-900 dark:text-neutral-50">
                            {stats.total_documents || 0}
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-neutral-600 dark:text-neutral-400 flex items-center">
                            <Layers className="mr-2 h-4 w-4" />
                            {t('search.stats.totalChunks')}
                          </span>
                          <span className="font-medium text-neutral-900 dark:text-neutral-50">
                            {stats.total_chunks || 0}
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-neutral-600 dark:text-neutral-400 flex items-center">
                            <Database className="mr-2 h-4 w-4" />
                            {t('search.stats.totalEmbeddings')}
                          </span>
                          <span className="font-medium text-neutral-900 dark:text-neutral-50">
                            {stats.total_embeddings || 0}
                          </span>
                        </div>
                      </div>
                    ) : (
                      <p className="text-sm text-neutral-600 dark:text-neutral-400">
                        {t('search.stats.loading')}
                      </p>
                    )}
                  </CardContent>
                </Card>
              </div>

              {/* Right Column - Results */}
              <div className="lg:col-span-2">
                {/* Results Header */}
                {results.length > 0 && (
                  <div className="mb-4 flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-neutral-900 dark:text-neutral-50">
                        {results.length === 1
                          ? t('search.resultsCountSingular')
                          : t('search.resultsCount', { count: results.length })}
                      </p>
                      <p className="text-xs text-neutral-600 dark:text-neutral-400">
                        {t('search.searchTime', { time: searchTime.toFixed(3) })}
                      </p>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleExportResults}
                    >
                      <Download className="mr-2 h-4 w-4" />
                      {t('common.export', 'Export CSV')}
                    </Button>
                  </div>
                )}

                {/* Empty State */}
                {!searching && results.length === 0 && query && (
                  <Card className="text-center py-12">
                    <CardContent>
                      <Search className="mx-auto h-12 w-12 text-neutral-400 mb-4" />
                      <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-50 mb-2">
                        {t('search.noResults')}
                      </h3>
                      <p className="text-neutral-600 dark:text-neutral-400">
                        {t('search.noResultsDescription')}
                      </p>
                    </CardContent>
                  </Card>
                )}

                {/* Results List */}
                <div className="space-y-4">
                  {results.map((result, index) => (
                    <Card key={`${result.chunk_id}-${index}`}>
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <CardTitle className="text-lg mb-2 flex items-center gap-2">
                              <FileText className="h-5 w-5 text-primary-600" />
                              {result.document_title}
                            </CardTitle>
                            <div className="flex items-center gap-2">
                              <Badge variant={getSimilarityBadge(result.similarity_score)}>
                                {t('search.result.similarity')}: {(result.similarity_score * 100).toFixed(1)}%
                              </Badge>
                              <Badge variant="outline">
                                {t('search.result.chunk')} #{result.chunk_index + 1}
                              </Badge>
                            </div>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-3">
                          <div className="text-sm text-neutral-700 dark:text-neutral-300 leading-relaxed">
                            {result.chunk_text}
                          </div>
                          <div className="pt-3 border-t border-neutral-200 dark:border-neutral-800">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => navigate('/documents')}
                              className="gap-2"
                            >
                              <ExternalLink className="h-4 w-4" />
                              {t('search.result.viewDocument')}
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
