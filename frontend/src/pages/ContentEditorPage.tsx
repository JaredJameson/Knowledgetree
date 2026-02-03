/**
 * ContentEditorPage - Full-Page Content Editor
 *
 * Features:
 * - Full-screen content editor (100% width)
 * - Advanced editing capabilities
 * - AI Tools sidebar
 * - Version history
 * - Quote extraction
 * - Templates
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  ArrowLeft,
  Save,
  Upload,
  Eye,
  EyeOff,
  Wand2,
  History,
  Quote,
  FileText
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useToast } from '@/hooks/use-toast';
import { ContentStatusBadge } from '@/components/content/ContentStatusBadge';
import { contentWorkbenchApi } from '@/lib/api/contentApi';
import type { CategoryWithContent } from '@/types/content';

export function ContentEditorPage() {
  const { categoryId } = useParams<{ categoryId: string }>();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { toast } = useToast();

  const [category, setCategory] = useState<CategoryWithContent | null>(null);
  const [draftContent, setDraftContent] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isPublishing, setIsPublishing] = useState(false);
  const [isPreviewMode, setIsPreviewMode] = useState(false);
  const [activeRightPanel, setActiveRightPanel] = useState<'ai' | 'versions' | 'quotes' | 'templates'>('ai');
  const [isAIProcessing, setIsAIProcessing] = useState(false);
  const [quotes, setQuotes] = useState<any[]>([]);
  const [isLoadingQuotes, setIsLoadingQuotes] = useState(false);
  const [versions, setVersions] = useState<any[]>([]);
  const [isLoadingVersions, setIsLoadingVersions] = useState(false);
  const [templates, setTemplates] = useState<any[]>([]);
  const [isLoadingTemplates, setIsLoadingTemplates] = useState(false);

  useEffect(() => {
    if (categoryId) {
      loadCategory();
    }
  }, [categoryId]);

  const loadCategory = async () => {
    if (!categoryId) return;

    setIsLoading(true);
    try {
      const response = await contentWorkbenchApi.getCategory(Number(categoryId));
      const data = response.data;
      setCategory(data);
      setDraftContent(data.draft_content || data.merged_content || '');
    } catch (error) {
      console.error('Failed to load category:', error);
      toast({
        title: t('contentWorkbench.errors.loadFailed'),
        variant: 'destructive'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveDraft = async () => {
    if (!categoryId) return;

    setIsSaving(true);
    try {
      const response = await contentWorkbenchApi.saveDraft(Number(categoryId), {
        draft_content: draftContent,
        auto_version: true
      });

      setCategory(response.data);
      toast({
        title: t('contentWorkbench.saved'),
        description: t('contentWorkbench.saveDraft')
      });
    } catch (error) {
      console.error('Failed to save draft:', error);
      toast({
        title: t('contentWorkbench.errors.saveFailed'),
        variant: 'destructive'
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handlePublish = async () => {
    if (!categoryId) return;

    setIsPublishing(true);
    try {
      const response = await contentWorkbenchApi.publish(Number(categoryId), {
        create_version: true
      });

      setCategory(response.data);
      toast({
        title: t('contentWorkbench.status.published'),
        description: t('contentWorkbench.publish')
      });
    } catch (error) {
      console.error('Failed to publish:', error);
      toast({
        title: t('contentWorkbench.errors.publishFailed'),
        variant: 'destructive'
      });
    } finally {
      setIsPublishing(false);
    }
  };

  // AI Operations Handlers
  const handleAIOperation = async (
    operation: 'summarize' | 'expand' | 'simplify' | 'rewrite' | 'extract' | 'outline',
    options?: any
  ) => {
    if (!categoryId || !draftContent.trim()) {
      toast({
        title: t('contentWorkbench.errors.noContent'),
        description: t('contentWorkbench.errors.addContentFirst'),
        variant: 'destructive'
      });
      return;
    }

    setIsAIProcessing(true);
    try {
      let result: string = '';

      switch (operation) {
        case 'summarize':
          const summarizeResponse = await contentWorkbenchApi.summarize({
            content: draftContent,
            max_length: options?.maxLength
          });
          result = summarizeResponse.data.result;
          break;

        case 'expand':
          const expandResponse = await contentWorkbenchApi.expand({
            content: draftContent,
            target_length: options?.targetLength
          });
          result = expandResponse.data.result;
          break;

        case 'simplify':
          const simplifyResponse = await contentWorkbenchApi.simplify({
            content: draftContent,
            reading_level: options?.readingLevel || 'intermediate'
          });
          result = simplifyResponse.data.result;
          break;

        case 'rewrite':
          const rewriteResponse = await contentWorkbenchApi.rewriteTone({
            content: draftContent,
            tone: options?.tone || 'professional',
            preserve_facts: true
          });
          result = rewriteResponse.data.result;
          break;

        case 'extract':
          await contentWorkbenchApi.extractQuotes(Number(categoryId), {
            content: draftContent,
            max_quotes: options?.maxQuotes || 10
          });
          toast({
            title: t('contentWorkbench.aiTools.success'),
            description: t('contentWorkbench.aiTools.quotesExtracted')
          });
          // Switch to quotes tab to show extracted quotes
          setActiveRightPanel('quotes');
          loadQuotes();
          return;

        case 'outline':
          const outlineResponse = await contentWorkbenchApi.generateOutline({
            topic: draftContent,
            depth: options?.depth || 2
          });
          result = outlineResponse.data.result;
          break;
      }

      // Update draft content with AI result
      setDraftContent(result);
      toast({
        title: t('contentWorkbench.aiTools.success'),
        description: t(`contentWorkbench.aiTools.${operation}Success`)
      });
    } catch (error) {
      console.error(`Failed to ${operation}:`, error);
      toast({
        title: t('contentWorkbench.aiTools.error'),
        description: t(`contentWorkbench.aiTools.${operation}Error`),
        variant: 'destructive'
      });
    } finally {
      setIsAIProcessing(false);
    }
  };

  const loadQuotes = async () => {
    if (!categoryId) return;

    setIsLoadingQuotes(true);
    try {
      const response = await contentWorkbenchApi.getQuotes(Number(categoryId));
      setQuotes(response.data);
    } catch (error) {
      console.error('Failed to load quotes:', error);
      toast({
        title: t('contentWorkbench.errors.loadFailed'),
        description: t('contentWorkbench.quotes.loadError'),
        variant: 'destructive'
      });
    } finally {
      setIsLoadingQuotes(false);
    }
  };

  const loadVersions = async () => {
    if (!categoryId) return;

    setIsLoadingVersions(true);
    try {
      const response = await contentWorkbenchApi.listVersions(Number(categoryId), 50, 0);
      setVersions(response.data);
    } catch (error) {
      console.error('Failed to load versions:', error);
      toast({
        title: t('contentWorkbench.errors.loadFailed'),
        description: t('contentWorkbench.versions.loadError'),
        variant: 'destructive'
      });
    } finally {
      setIsLoadingVersions(false);
    }
  };

  const handleRestoreVersion = async (versionNumber: number) => {
    if (!categoryId) return;

    try {
      const response = await contentWorkbenchApi.restoreVersion(Number(categoryId), {
        version_number: versionNumber,
        create_new_version: true
      });

      setCategory(response.data);
      setDraftContent(response.data.draft_content || response.data.merged_content || '');
      toast({
        title: t('contentWorkbench.versions.restored'),
        description: t('contentWorkbench.versions.restoredDescription')
      });
      
      // Reload versions to show the new version
      loadVersions();
    } catch (error) {
      console.error('Failed to restore version:', error);
      toast({
        title: t('contentWorkbench.errors.restoreFailed'),
        description: t('contentWorkbench.versions.restoreError'),
        variant: 'destructive'
      });
    }
  };

  // Load quotes when quotes tab is activated
  useEffect(() => {
    if (activeRightPanel === 'quotes' && categoryId) {
      loadQuotes();
    }
  }, [activeRightPanel, categoryId]);

  const loadTemplates = async () => {
    setIsLoadingTemplates(true);
    try {
      const response = await contentWorkbenchApi.listTemplates();
      setTemplates(response.data);
    } catch (error) {
      console.error('Failed to load templates:', error);
      toast({
        title: t('contentWorkbench.errors.loadFailed'),
        description: t('contentWorkbench.templates.loadError'),
        variant: 'destructive'
      });
    } finally {
      setIsLoadingTemplates(false);
    }
  };

  const handleApplyTemplate = (template: any) => {
    // Generate content from template sections
    const templateContent = template.structure.sections
      .sort((a: any, b: any) => a.order - b.order)
      .map((section: any) => `## ${section.title}

${section.prompt}

`)
      .join('');

    setDraftContent(templateContent);
    toast({
      title: t('contentWorkbench.templates.applied'),
      description: `${t('contentWorkbench.templates.appliedDescription')}: ${template.name}`
    });
  };

  // Load versions when versions tab is activated
  useEffect(() => {
    if (activeRightPanel === 'versions' && categoryId) {
      loadVersions();
    }
  }, [activeRightPanel, categoryId]);

  // Load templates when templates tab is activated
  useEffect(() => {
    if (activeRightPanel === 'templates') {
      loadTemplates();
    }
  }, [activeRightPanel]);

  const handleBack = () => {
    navigate(-1);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p className="text-muted-foreground">{t('common.loading')}</p>
      </div>
    );
  }

  if (!category) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <p className="text-muted-foreground">{t('contentWorkbench.errors.loadFailed')}</p>
          <Button variant="outline" onClick={handleBack} className="mt-4">
            <ArrowLeft className="h-4 w-4 mr-2" />
            {t('common.back')}
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <header className="border-b bg-background">
        <div className="flex items-center justify-between px-6 py-4">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" onClick={handleBack}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              {t('common.back')}
            </Button>

            <Separator orientation="vertical" className="h-6" />

            <div>
              <h1 className="text-lg font-semibold">{category.name}</h1>
              <ContentStatusBadge
                status={category.content_status as any}
                publishedAt={category.published_at}
                className="mt-1"
              />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsPreviewMode(!isPreviewMode)}
            >
              {isPreviewMode ? (
                <>
                  <EyeOff className="h-4 w-4 mr-2" />
                  {t('contentWorkbench.editMode')}
                </>
              ) : (
                <>
                  <Eye className="h-4 w-4 mr-2" />
                  {t('contentWorkbench.preview')}
                </>
              )}
            </Button>

            <Separator orientation="vertical" className="h-6" />

            <Button
              variant="outline"
              size="sm"
              onClick={handleSaveDraft}
              disabled={isSaving}
            >
              <Save className="h-4 w-4 mr-2" />
              {isSaving ? t('contentWorkbench.saving') : t('contentWorkbench.saveDraft')}
            </Button>

            <Button
              variant="default"
              size="sm"
              onClick={handlePublish}
              disabled={isPublishing}
            >
              <Upload className="h-4 w-4 mr-2" />
              {isPublishing ? t('contentWorkbench.publishing') : t('contentWorkbench.publish')}
            </Button>
          </div>
        </div>
      </header>

      {/* Main content area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Editor area (70%) */}
        <div className="flex-1 flex flex-col border-r">
          <ScrollArea className="flex-1">
            <div className="p-6">
              {isPreviewMode ? (
                <div
                  className="prose prose-sm max-w-none dark:prose-invert"
                  dangerouslySetInnerHTML={{
                    __html: draftContent.replace(/\n/g, '<br />')
                  }}
                />
              ) : (
                <div className="space-y-4">
                  <Textarea
                    value={draftContent}
                    onChange={(e) => setDraftContent(e.target.value)}
                    placeholder={t('contentWorkbench.editor.placeholder')}
                    className="min-h-[calc(100vh-300px)] font-mono text-sm resize-none"
                  />

                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    <span>
                      {t('contentWorkbench.editor.characterCount')}: {draftContent.length}
                    </span>
                    <span>
                      {t('contentWorkbench.editor.wordCount')}: {draftContent.split(/\s+/).filter(w => w).length}
                    </span>
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>
        </div>

        {/* Right sidebar (30%) */}
        <div className="w-[30%] flex flex-col bg-muted/10">
          <Tabs value={activeRightPanel} onValueChange={(v) => setActiveRightPanel(v as any)} className="flex-1 flex flex-col">
            <TabsList className="m-4 grid grid-cols-4">
              <TabsTrigger value="ai" className="text-xs">
                <Wand2 className="h-3 w-3" />
              </TabsTrigger>
              <TabsTrigger value="versions" className="text-xs">
                <History className="h-3 w-3" />
              </TabsTrigger>
              <TabsTrigger value="quotes" className="text-xs">
                <Quote className="h-3 w-3" />
              </TabsTrigger>
              <TabsTrigger value="templates" className="text-xs">
                <FileText className="h-3 w-3" />
              </TabsTrigger>
            </TabsList>

            <ScrollArea className="flex-1">
              <div className="px-4 pb-4">
                <TabsContent value="ai" className="mt-0">
                  <h3 className="font-semibold text-sm mb-3">
                    {t('contentWorkbench.aiTools.title')}
                  </h3>
                  <p className="text-xs text-muted-foreground mb-4">
                    {t('contentWorkbench.aiTools.description')}
                  </p>

                  <div className="space-y-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full justify-start"
                      onClick={() => handleAIOperation('summarize')}
                      disabled={isAIProcessing || !draftContent.trim()}
                    >
                      {t('contentWorkbench.aiTools.summarize')}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full justify-start"
                      onClick={() => handleAIOperation('expand')}
                      disabled={isAIProcessing || !draftContent.trim()}
                    >
                      {t('contentWorkbench.aiTools.expand')}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full justify-start"
                      onClick={() => handleAIOperation('simplify')}
                      disabled={isAIProcessing || !draftContent.trim()}
                    >
                      {t('contentWorkbench.aiTools.simplify')}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full justify-start"
                      onClick={() => handleAIOperation('rewrite', { tone: 'professional' })}
                      disabled={isAIProcessing || !draftContent.trim()}
                    >
                      {t('contentWorkbench.aiTools.rewriteTone')}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full justify-start"
                      onClick={() => handleAIOperation('extract')}
                      disabled={isAIProcessing || !draftContent.trim()}
                    >
                      {t('contentWorkbench.aiTools.extractQuotes')}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full justify-start"
                      onClick={() => handleAIOperation('outline')}
                      disabled={isAIProcessing || !draftContent.trim()}
                    >
                      {t('contentWorkbench.aiTools.generateOutline')}
                    </Button>
                  </div>

                  {isAIProcessing && (
                    <p className="text-xs text-muted-foreground italic mt-4">
                      {t('contentWorkbench.aiTools.processing')}
                    </p>
                  )}
                </TabsContent>

                <TabsContent value="versions" className="mt-0">
                  <h3 className="font-semibold text-sm mb-3">
                    {t('contentWorkbench.versions.title')}
                  </h3>

                  {isLoadingVersions ? (
                    <p className="text-xs text-muted-foreground">
                      {t('common.loading')}
                    </p>
                  ) : versions.length === 0 ? (
                    <p className="text-xs text-muted-foreground">
                      {t('contentWorkbench.versions.noVersions')}
                    </p>
                  ) : (
                    <div className="space-y-2">
                      {versions.map((version) => (
                        <div
                          key={version.id}
                          className="p-3 bg-muted/50 rounded-md border"
                        >
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-sm font-semibold">
                              {t('contentWorkbench.versions.version')} {version.version_number}
                            </span>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleRestoreVersion(version.version_number)}
                              className="h-7 text-xs"
                            >
                              {t('contentWorkbench.versions.restore')}
                            </Button>
                          </div>
                          <p className="text-xs text-muted-foreground">
                            {new Date(version.created_at).toLocaleString('pl-PL')}
                          </p>
                          {version.change_summary && (
                            <p className="text-xs text-muted-foreground mt-1">
                              {version.change_summary}
                            </p>
                          )}
                          <p className="text-xs text-muted-foreground mt-2 truncate">
                            {version.content?.substring(0, 100)}...
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </TabsContent>

                <TabsContent value="quotes" className="mt-0">
                  <h3 className="font-semibold text-sm mb-3">
                    {t('contentWorkbench.quotes.title')}
                  </h3>

                  {isLoadingQuotes ? (
                    <p className="text-xs text-muted-foreground">
                      {t('common.loading')}
                    </p>
                  ) : quotes.length === 0 ? (
                    <div className="space-y-2">
                      <p className="text-xs text-muted-foreground">
                        {t('contentWorkbench.quotes.noQuotes')}
                      </p>
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full"
                        onClick={() => handleAIOperation('extract')}
                        disabled={isAIProcessing || !draftContent.trim()}
                      >
                        {t('contentWorkbench.aiTools.extractQuotes')}
                      </Button>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {quotes.map((quote, index) => (
                        <div
                          key={quote.id || index}
                          className="p-3 bg-muted/50 rounded-md border"
                        >
                          <p className="text-sm font-medium mb-2">"{quote.quote_text}"</p>
                          {quote.quote_type && (
                            <span className="inline-block px-2 py-0.5 text-xs bg-primary/10 text-primary rounded">
                              {quote.quote_type}
                            </span>
                          )}
                          {(quote.context_before || quote.context_after) && (
                            <p className="text-xs text-muted-foreground mt-2">
                              {quote.context_before && `...${quote.context_before} `}
                              <span className="font-semibold">[quote]</span>
                              {quote.context_after && ` ${quote.context_after}...`}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </TabsContent>

                <TabsContent value="templates" className="mt-0">
                  <h3 className="font-semibold text-sm mb-3">
                    {t('contentWorkbench.templates.title')}
                  </h3>

                  {isLoadingTemplates ? (
                    <p className="text-xs text-muted-foreground">
                      {t('common.loading')}
                    </p>
                  ) : templates.length === 0 ? (
                    <p className="text-xs text-muted-foreground">
                      {t('contentWorkbench.templates.noTemplates')}
                    </p>
                  ) : (
                    <div className="space-y-2">
                      {templates.map((template) => (
                        <div key={template.id} className="p-3 bg-muted/50 rounded-md border">
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex-1">
                              <h4 className="text-sm font-semibold mb-1">{template.name}</h4>
                              {template.description && (
                                <p className="text-xs text-muted-foreground mb-2">
                                  {template.description}
                                </p>
                              )}
                              {template.template_type && (
                                <span className="inline-block px-2 py-0.5 text-xs bg-primary/10 text-primary rounded">
                                  {template.template_type}
                                </span>
                              )}
                            </div>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleApplyTemplate(template)}
                              className="ml-2 h-8 text-xs"
                            >
                              {t('contentWorkbench.templates.apply')}
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </TabsContent>
              </div>
            </ScrollArea>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
