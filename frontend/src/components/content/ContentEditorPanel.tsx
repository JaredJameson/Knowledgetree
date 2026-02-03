/**
 * ContentEditorPanel - Sliding Panel Content Editor
 *
 * Features:
 * - Slides in from right (60% width)
 * - Draft/Publish workflow
 * - AI Tools integration
 * - Version history access
 * - "Open Full Editor" button
 */

import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { X, Save, Upload, Maximize2, History, Wand2 } from 'lucide-react';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useToast } from '@/hooks/use-toast';
import { contentWorkbenchApi } from '@/lib/api/contentApi';
import type { CategoryWithContent } from '@/types/content';

interface ContentEditorPanelProps {
  categoryId: number | null;
  isOpen: boolean;
  onClose: () => void;
  onOpenFullEditor?: (categoryId: number) => void;
}

export function ContentEditorPanel({
  categoryId,
  isOpen,
  onClose,
  onOpenFullEditor
}: ContentEditorPanelProps) {
  const { t } = useTranslation();
  const { toast } = useToast();

  const [category, setCategory] = useState<CategoryWithContent | null>(null);
  const [draftContent, setDraftContent] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isPublishing, setIsPublishing] = useState(false);
  const [activeTab, setActiveTab] = useState('editor');
  const [isAIProcessing, setIsAIProcessing] = useState(false);

  // Load category data when categoryId changes
  useEffect(() => {
    if (categoryId && isOpen) {
      loadCategory();
    }
  }, [categoryId, isOpen]);

  const loadCategory = async () => {
    if (!categoryId) return;

    setIsLoading(true);
    try {
      const response = await contentWorkbenchApi.getCategory(categoryId);
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
      const response = await contentWorkbenchApi.saveDraft(categoryId, {
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
      const response = await contentWorkbenchApi.publish(categoryId, {
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

  const handleOpenFullEditor = () => {
    if (categoryId && onOpenFullEditor) {
      onOpenFullEditor(categoryId);
      onClose();
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
          await contentWorkbenchApi.extractQuotes(categoryId, {
            content: draftContent,
            max_quotes: options?.maxQuotes || 10
          });
          toast({
            title: t('contentWorkbench.aiTools.success'),
            description: t('contentWorkbench.aiTools.quotesExtracted')
          });
          // Switch to versions tab (panel doesn't have quotes tab)
          setActiveTab('versions');
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

  if (!categoryId) return null;

  return (
    <Sheet open={isOpen} onOpenChange={onClose}>
      <SheetContent side="right" className="w-[60%] sm:max-w-none p-0 flex flex-col">
        {/* Header */}
        <SheetHeader className="px-6 py-4 border-b">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <SheetTitle className="text-lg font-semibold">
                {category?.name || t('contentWorkbench.title')}
              </SheetTitle>
              <SheetDescription className="flex items-center gap-2 mt-1">
                <Badge
                  variant={category?.content_status === 'published' ? 'default' : 'secondary'}
                >
                  {category?.content_status
                    ? t(`contentWorkbench.status.${category.content_status}`)
                    : t('contentWorkbench.status.draft')
                  }
                </Badge>
                {category?.published_at && (
                  <span className="text-xs text-muted-foreground">
                    {new Date(category.published_at).toLocaleDateString('pl-PL')}
                  </span>
                )}
              </SheetDescription>
            </div>

            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-2 mt-3">
            <Button
              variant="outline"
              size="sm"
              onClick={handleSaveDraft}
              disabled={isSaving || isLoading}
            >
              <Save className="h-4 w-4 mr-2" />
              {isSaving ? t('contentWorkbench.saving') : t('contentWorkbench.saveDraft')}
            </Button>

            <Button
              variant="default"
              size="sm"
              onClick={handlePublish}
              disabled={isPublishing || isLoading}
            >
              <Upload className="h-4 w-4 mr-2" />
              {isPublishing ? t('contentWorkbench.publishing') : t('contentWorkbench.publish')}
            </Button>

            <div className="flex-1" />

            <Button
              variant="outline"
              size="sm"
              onClick={handleOpenFullEditor}
            >
              <Maximize2 className="h-4 w-4 mr-2" />
              {t('contentWorkbench.openFullEditor')}
            </Button>
          </div>
        </SheetHeader>

        {/* Main content area with tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
          <TabsList className="mx-6 mt-4">
            <TabsTrigger value="editor">
              {t('contentWorkbench.editMode')}
            </TabsTrigger>
            <TabsTrigger value="ai-tools">
              <Wand2 className="h-4 w-4 mr-2" />
              {t('contentWorkbench.aiTools.title')}
            </TabsTrigger>
            <TabsTrigger value="versions">
              <History className="h-4 w-4 mr-2" />
              {t('contentWorkbench.versions.title')}
            </TabsTrigger>
          </TabsList>

          {/* Editor Tab */}
          <TabsContent value="editor" className="flex-1 px-6 mt-0">
            <ScrollArea className="h-full py-4">
              {isLoading ? (
                <div className="flex items-center justify-center h-64">
                  <p className="text-muted-foreground">{t('common.loading')}</p>
                </div>
              ) : (
                <div className="space-y-4">
                  <Textarea
                    value={draftContent}
                    onChange={(e) => setDraftContent(e.target.value)}
                    placeholder={t('contentWorkbench.editor.placeholder')}
                    className="min-h-[500px] font-mono text-sm"
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
            </ScrollArea>
          </TabsContent>

          {/* AI Tools Tab */}
          <TabsContent value="ai-tools" className="flex-1 px-6 mt-0">
            <ScrollArea className="h-full py-4">
              <div className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  {t('contentWorkbench.aiTools.description')}
                </p>

                <div className="grid grid-cols-2 gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleAIOperation('summarize')}
                    disabled={isAIProcessing || !draftContent.trim()}
                  >
                    {t('contentWorkbench.aiTools.summarize')}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleAIOperation('expand')}
                    disabled={isAIProcessing || !draftContent.trim()}
                  >
                    {t('contentWorkbench.aiTools.expand')}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleAIOperation('simplify')}
                    disabled={isAIProcessing || !draftContent.trim()}
                  >
                    {t('contentWorkbench.aiTools.simplify')}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleAIOperation('rewrite', { tone: 'professional' })}
                    disabled={isAIProcessing || !draftContent.trim()}
                  >
                    {t('contentWorkbench.aiTools.rewriteTone')}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleAIOperation('extract')}
                    disabled={isAIProcessing || !draftContent.trim()}
                  >
                    {t('contentWorkbench.aiTools.extractQuotes')}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleAIOperation('outline')}
                    disabled={isAIProcessing || !draftContent.trim()}
                  >
                    {t('contentWorkbench.aiTools.generateOutline')}
                  </Button>
                </div>

                {isAIProcessing && (
                  <p className="text-xs text-muted-foreground italic">
                    {t('contentWorkbench.aiTools.processing')}
                  </p>
                )}
              </div>
            </ScrollArea>
          </TabsContent>

          {/* Versions Tab */}
          <TabsContent value="versions" className="flex-1 px-6 mt-0">
            <ScrollArea className="h-full py-4">
              <div className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  {t('contentWorkbench.versions.description')}
                </p>

                <p className="text-xs text-muted-foreground italic">
                  {/* TODO: Implement version history in next step */}
                  Historia wersji będzie dostępna wkrótce
                </p>
              </div>
            </ScrollArea>
          </TabsContent>
        </Tabs>
      </SheetContent>
    </Sheet>
  );
}
