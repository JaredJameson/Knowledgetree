/**
 * QuotesPanel - Extracted Quotes Management
 *
 * Features:
 * - Display extracted quotes
 * - Filter by quote type
 * - Copy quotes
 * - View context
 */

import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Quote, Copy, Filter, Loader2, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { contentWorkbenchApi } from '@/lib/api/contentApi';
import type { ExtractedQuote, QuoteType } from '@/types/content';

interface QuotesPanelProps {
  categoryId: number;
  className?: string;
}

export function QuotesPanel({ categoryId, className }: QuotesPanelProps) {
  const { t } = useTranslation();
  const { toast } = useToast();

  const [quotes, setQuotes] = useState<ExtractedQuote[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [filterType, setFilterType] = useState<QuoteType | 'all'>('all');
  const [copiedId, setCopiedId] = useState<number | null>(null);

  useEffect(() => {
    loadQuotes();
  }, [categoryId]);

  const loadQuotes = async () => {
    setIsLoading(true);
    try {
      const response = await contentWorkbenchApi.getQuotes(categoryId);
      setQuotes(response.data);
    } catch (error) {
      console.error('Failed to load quotes:', error);
      toast({
        title: t('contentWorkbench.errors.quotesFailed'),
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopyQuote = async (quote: ExtractedQuote) => {
    try {
      await navigator.clipboard.writeText(quote.quote_text);
      setCopiedId(quote.id);
      setTimeout(() => setCopiedId(null), 2000);
      toast({
        title: t('contentWorkbench.quotes.copied', 'Copied to clipboard'),
      });
    } catch (error) {
      console.error('Failed to copy quote:', error);
      toast({
        title: t('common.error'),
        variant: 'destructive',
      });
    }
  };

  const filteredQuotes =
    filterType === 'all'
      ? quotes
      : quotes.filter((q) => q.quote_type === filterType);

  const getQuoteTypeVariant = (type: QuoteType | null) => {
    switch (type) {
      case 'fact':
        return 'default';
      case 'opinion':
        return 'secondary';
      case 'definition':
        return 'outline';
      case 'statistic':
        return 'default';
      case 'example':
        return 'secondary';
      default:
        return 'outline';
    }
  };

  return (
    <div className={className}>
      <div className="space-y-4">
        <div>
          <h3 className="font-semibold text-sm mb-3 flex items-center gap-2">
            <Quote className="h-4 w-4" />
            {t('contentWorkbench.quotes.title')}
          </h3>
          <p className="text-xs text-muted-foreground mb-4">
            {t('contentWorkbench.quotes.description')}
          </p>
        </div>

        {/* Filter */}
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <Select
            value={filterType}
            onValueChange={(value) => setFilterType(value as QuoteType | 'all')}
          >
            <SelectTrigger className="h-8 text-xs flex-1">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">
                {t('contentWorkbench.quotes.allTypes', 'All Types')}
              </SelectItem>
              <SelectItem value="fact">
                {t('contentWorkbench.quotes.types.fact')}
              </SelectItem>
              <SelectItem value="opinion">
                {t('contentWorkbench.quotes.types.opinion')}
              </SelectItem>
              <SelectItem value="definition">
                {t('contentWorkbench.quotes.types.definition')}
              </SelectItem>
              <SelectItem value="statistic">
                {t('contentWorkbench.quotes.types.statistic')}
              </SelectItem>
              <SelectItem value="example">
                {t('contentWorkbench.quotes.types.example')}
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Quotes list */}
        <ScrollArea className="h-[400px]">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : filteredQuotes.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-sm text-muted-foreground mb-2">
                {t('contentWorkbench.quotes.noQuotes')}
              </p>
              <p className="text-xs text-muted-foreground">
                {t('contentWorkbench.quotes.noQuotesDescription')}
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredQuotes.map((quote) => (
                <div
                  key={quote.id}
                  className="border rounded-lg p-3 space-y-2 hover:bg-accent/50 transition-colors"
                >
                  {/* Quote header */}
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      {quote.quote_type && (
                        <Badge
                          variant={getQuoteTypeVariant(quote.quote_type)}
                          className="text-xs mb-2"
                        >
                          {t(
                            `contentWorkbench.quotes.types.${quote.quote_type}`
                          )}
                        </Badge>
                      )}
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 w-7 p-0"
                      onClick={() => handleCopyQuote(quote)}
                      title={t('contentWorkbench.quotes.copyQuote')}
                    >
                      {copiedId === quote.id ? (
                        <Check className="h-3 w-3 text-green-500" />
                      ) : (
                        <Copy className="h-3 w-3" />
                      )}
                    </Button>
                  </div>

                  {/* Quote text */}
                  <div className="bg-muted/30 p-3 rounded border-l-2 border-primary">
                    <p className="text-sm italic">{quote.quote_text}</p>
                  </div>

                  {/* Context */}
                  {(quote.context_before || quote.context_after) && (
                    <div className="space-y-1 text-xs text-muted-foreground">
                      {quote.context_before && (
                        <div>
                          <span className="font-medium">
                            {t('contentWorkbench.quotes.contextBefore', 'Before')}
                            :{' '}
                          </span>
                          <span>{quote.context_before}</span>
                        </div>
                      )}
                      {quote.context_after && (
                        <div>
                          <span className="font-medium">
                            {t('contentWorkbench.quotes.contextAfter', 'After')}
                            :{' '}
                          </span>
                          <span>{quote.context_after}</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </ScrollArea>

        {/* Quote count */}
        {filteredQuotes.length > 0 && (
          <div className="text-xs text-muted-foreground text-center pt-2 border-t">
            {filteredQuotes.length}{' '}
            {filteredQuotes.length === 1
              ? t('contentWorkbench.quotes.quote', 'quote')
              : t('contentWorkbench.quotes.quotes', 'quotes')}
          </div>
        )}
      </div>
    </div>
  );
}
