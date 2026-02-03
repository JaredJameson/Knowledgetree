/**
 * AIToolsPanel - AI-Powered Content Operations
 *
 * Features:
 * - 7 AI operations (summarize, expand, simplify, rewrite tone, extract quotes, generate outline)
 * - Tone selection for rewriting
 * - Reading level selection
 * - Operation status tracking
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Wand2,
  Sparkles,
  FileText,
  Quote,
  List,
  Loader2,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import { contentWorkbenchApi } from '@/lib/api/contentApi';
import type { ToneType, ReadingLevel } from '@/types/content';

interface AIToolsPanelProps {
  categoryId: number;
  content: string;
  onContentUpdate: (newContent: string) => void;
  className?: string;
}

export function AIToolsPanel({
  categoryId,
  content,
  onContentUpdate,
  className,
}: AIToolsPanelProps) {
  const { t } = useTranslation();
  const { toast } = useToast();

  const [isProcessing, setIsProcessing] = useState(false);
  const [selectedTone, setSelectedTone] = useState<ToneType>('professional');
  const [selectedLevel, setSelectedLevel] = useState<ReadingLevel>('intermediate');

  const handleAIOperation = async (
    operation: 'summarize' | 'expand' | 'simplify' | 'rewriteTone' | 'extractQuotes' | 'generateOutline'
  ) => {
    if (!content.trim()) {
      toast({
        title: t('contentWorkbench.errors.noContent'),
        description: t('contentWorkbench.errors.noContentDescription'),
        variant: 'destructive',
      });
      return;
    }

    setIsProcessing(true);
    try {
      let response;

      switch (operation) {
        case 'summarize':
          response = await contentWorkbenchApi.summarize({
            category_id: categoryId,
            text: content,
          });
          break;

        case 'expand':
          response = await contentWorkbenchApi.expand({
            category_id: categoryId,
            text: content,
          });
          break;

        case 'simplify':
          response = await contentWorkbenchApi.simplify({
            category_id: categoryId,
            text: content,
            reading_level: selectedLevel,
          });
          break;

        case 'rewriteTone':
          response = await contentWorkbenchApi.rewriteTone({
            category_id: categoryId,
            text: content,
            tone: selectedTone,
          });
          break;

        case 'extractQuotes':
          await contentWorkbenchApi.extractQuotes(categoryId, {
            category_id: categoryId,
            text: content,
          });
          toast({
            title: t('contentWorkbench.success'),
            description: t('contentWorkbench.aiTools.quotesExtracted'),
          });
          return; // Don't update content for quote extraction

        case 'generateOutline':
          response = await contentWorkbenchApi.generateOutline({
            category_id: categoryId,
            text: content,
          });
          break;

        default:
          throw new Error('Unknown operation');
      }

      if (response && response.data.result) {
        onContentUpdate(response.data.result);
        toast({
          title: t('contentWorkbench.success'),
          description: t(`contentWorkbench.aiTools.${operation}Success`),
        });
      }
    } catch (error) {
      console.error(`AI operation ${operation} failed:`, error);
      toast({
        title: t('contentWorkbench.errors.aiFailed'),
        description: t(`contentWorkbench.errors.${operation}Failed`),
        variant: 'destructive',
      });
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className={className}>
      <div className="space-y-4">
        <div>
          <h3 className="font-semibold text-sm mb-3">
            {t('contentWorkbench.aiTools.title')}
          </h3>
          <p className="text-xs text-muted-foreground mb-4">
            {t('contentWorkbench.aiTools.description')}
          </p>
        </div>

        {/* AI Operations */}
        <div className="space-y-2">
          <Button
            variant="outline"
            size="sm"
            className="w-full justify-start"
            onClick={() => handleAIOperation('summarize')}
            disabled={isProcessing}
          >
            <FileText className="h-4 w-4 mr-2" />
            {t('contentWorkbench.aiTools.summarize')}
          </Button>

          <Button
            variant="outline"
            size="sm"
            className="w-full justify-start"
            onClick={() => handleAIOperation('expand')}
            disabled={isProcessing}
          >
            <Sparkles className="h-4 w-4 mr-2" />
            {t('contentWorkbench.aiTools.expand')}
          </Button>

          <Button
            variant="outline"
            size="sm"
            className="w-full justify-start"
            onClick={() => handleAIOperation('simplify')}
            disabled={isProcessing}
          >
            <Wand2 className="h-4 w-4 mr-2" />
            {t('contentWorkbench.aiTools.simplify')}
          </Button>
        </div>

        {/* Simplify Options */}
        <div className="space-y-2">
          <Label className="text-xs">
            {t('contentWorkbench.aiTools.readingLevel')}
          </Label>
          <Select
            value={selectedLevel}
            onValueChange={(value) => setSelectedLevel(value as ReadingLevel)}
          >
            <SelectTrigger className="h-8 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="basic">
                {t('contentWorkbench.readingLevels.basic')}
              </SelectItem>
              <SelectItem value="intermediate">
                {t('contentWorkbench.readingLevels.intermediate')}
              </SelectItem>
              <SelectItem value="advanced">
                {t('contentWorkbench.readingLevels.advanced')}
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Tone Rewriting */}
        <div className="space-y-2">
          <Label className="text-xs">
            {t('contentWorkbench.aiTools.rewriteTone')}
          </Label>
          <Select
            value={selectedTone}
            onValueChange={(value) => setSelectedTone(value as ToneType)}
          >
            <SelectTrigger className="h-8 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="professional">
                {t('contentWorkbench.tones.professional')}
              </SelectItem>
              <SelectItem value="casual">
                {t('contentWorkbench.tones.casual')}
              </SelectItem>
              <SelectItem value="technical">
                {t('contentWorkbench.tones.technical')}
              </SelectItem>
              <SelectItem value="friendly">
                {t('contentWorkbench.tones.friendly')}
              </SelectItem>
              <SelectItem value="formal">
                {t('contentWorkbench.tones.formal')}
              </SelectItem>
              <SelectItem value="conversational">
                {t('contentWorkbench.tones.conversational')}
              </SelectItem>
            </SelectContent>
          </Select>

          <Button
            variant="outline"
            size="sm"
            className="w-full justify-start"
            onClick={() => handleAIOperation('rewriteTone')}
            disabled={isProcessing}
          >
            <Wand2 className="h-4 w-4 mr-2" />
            {t('contentWorkbench.aiTools.applyTone')}
          </Button>
        </div>

        {/* Additional Operations */}
        <div className="space-y-2">
          <Button
            variant="outline"
            size="sm"
            className="w-full justify-start"
            onClick={() => handleAIOperation('extractQuotes')}
            disabled={isProcessing}
          >
            <Quote className="h-4 w-4 mr-2" />
            {t('contentWorkbench.aiTools.extractQuotes')}
          </Button>

          <Button
            variant="outline"
            size="sm"
            className="w-full justify-start"
            onClick={() => handleAIOperation('generateOutline')}
            disabled={isProcessing}
          >
            <List className="h-4 w-4 mr-2" />
            {t('contentWorkbench.aiTools.generateOutline')}
          </Button>
        </div>

        {/* Processing indicator */}
        {isProcessing && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground pt-2">
            <Loader2 className="h-3 w-3 animate-spin" />
            {t('contentWorkbench.aiTools.processing')}
          </div>
        )}
      </div>
    </div>
  );
}
