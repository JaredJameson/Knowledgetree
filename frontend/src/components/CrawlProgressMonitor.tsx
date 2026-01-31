/**
 * CrawlProgressMonitor - Real-time progress monitoring for web crawl jobs
 *
 * Polls backend API for Celery task progress and displays:
 * - Progress bar (0-100%)
 * - Current step and status message
 * - Auto-refreshes every 2 seconds during active crawling
 */

import { useEffect, useState } from 'react';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, CheckCircle2, XCircle, Clock } from 'lucide-react';
import { useTranslation } from 'react-i18next';

interface CrawlProgress {
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'unknown';
  progress: number;
  step?: string;
  message?: string;
  current?: number;
  total?: number;
  error?: string;
}

interface CrawlProgressMonitorProps {
  jobId: number;
  onComplete?: () => void; // Callback when crawling completes
  onError?: (error: string) => void; // Callback on failure
}

export function CrawlProgressMonitor({
  jobId,
  onComplete,
  onError
}: CrawlProgressMonitorProps) {
  const { t } = useTranslation();
  const [progress, setProgress] = useState<CrawlProgress>({
    status: 'pending',
    progress: 0,
    message: t('crawl.starting')
  });

  // Translate backend progress messages to current language
  const translateProgressMessage = (message: string): string => {
    if (!message) return '';

    // AgenticBrowser messages (autonomous browsing)
    if (message.includes('Observing page:')) {
      const urlMatch = message.match(/Observing page: (.+)/);
      const url = urlMatch ? urlMatch[1] : '';
      return t('crawl.messages.observingPage', 'Obserwowanie strony') + ': ' + url;
    }
    if (message.includes('AI analyzing page')) {
      const match = message.match(/\((\d+)\/(\d+)\)/);
      if (match) {
        return t('crawl.messages.analyzingPage', 'AI analizuje stronę') + ` (${match[1]}/${match[2]})`;
      }
      return t('crawl.messages.analyzingPage', 'AI analizuje stronę');
    }
    if (message.includes('Content extracted from page')) {
      const match = message.match(/page (\d+)/);
      const pageNum = match ? match[1] : '';
      return t('crawl.messages.extractedPage', 'Wyodrębniono treść') + (pageNum ? ` ze strony ${pageNum}` : '');
    }
    if (message.includes('Browsing page:')) {
      const urlMatch = message.match(/Browsing page: (.+)/);
      const url = urlMatch ? urlMatch[1] : '';
      return t('crawl.messages.browsingPage', 'Przeglądanie autonomiczne') + ': ' + url;
    }

    // Link Discovery messages
    if (message.includes('Link Discovery')) {
      if (message.includes('Analyzing page')) {
        return t('crawl.messages.analyzingLinks', 'Analizowanie strony w poszukiwaniu linków...');
      }
      if (message.includes('Found') && message.includes('filtering with AI')) {
        const match = message.match(/Found (\d+) links/);
        const count = match ? match[1] : '0';
        return t('crawl.messages.filteringLinks', `Znaleziono ${count} linków, filtrowanie przez AI...`);
      }
      if (message.includes('Expanded from')) {
        const match = message.match(/Expanded from \d+ URL to (\d+) URLs/);
        const total = match ? match[1] : '0';
        return t('crawl.messages.expandedUrls', `Rozszerzono do ${total} URLi`);
      }
    }

    // Content Acquisition messages
    if (message.includes('Acquiring content from')) {
      const match = message.match(/Acquiring content from (\d+) URL/);
      const count = match ? match[1] : '0';
      return t('crawl.messages.acquiringContent', `Pobieranie treści z ${count} URLi...`);
    }

    // Scraping messages
    if (message.includes('Scraping URL')) {
      const match = message.match(/Scraping URL (\d+)\/(\d+)/);
      if (match) {
        return t('crawl.messages.scrapingUrl', `Pobieranie URL ${match[1]}/${match[2]}...`);
      }
    }

    // AI Extraction messages
    if (message.includes('AI extraction')) {
      if (message.includes('Extracting structured')) {
        return t('crawl.messages.extractingStructured', 'Wyodrębnianie strukturalnych danych przez AI...');
      }
      if (message.includes('Generating insights')) {
        return t('crawl.messages.generatingInsights', 'Generowanie insights przez AI...');
      }
    }

    // Document Creation messages
    if (message.includes('Creating document')) {
      return t('crawl.messages.creatingDocument', 'Tworzenie dokumentu...');
    }
    if (message.includes('Document created successfully')) {
      return t('crawl.messages.documentCreated', 'Dokument utworzony pomyślnie');
    }

    // Chunking messages
    if (message.includes('Chunking content')) {
      return t('crawl.messages.chunkingContent', 'Podział treści na fragmenty...');
    }
    if (message.includes('Generated') && message.includes('embeddings')) {
      const match = message.match(/Generated (\d+)\/(\d+) embeddings/);
      if (match) {
        return t('crawl.messages.generatingEmbeddings', `Generowanie embeddingów ${match[1]}/${match[2]}...`);
      }
    }

    // Agentic crawl messages
    if (message.includes('Processing content with AI agents')) {
      return t('crawl.messages.processingWithAI', 'Przetwarzanie treści przez agentów AI...');
    }
    if (message.includes('Preparing to extract with prompt')) {
      return t('crawl.messages.preparingExtraction', 'Przygotowanie do ekstrakcji...');
    }
    if (message.includes('Extracted') && message.includes('entities') && message.includes('insights')) {
      const entityMatch = message.match(/(\d+) entities/);
      const insightMatch = message.match(/(\d+) insights/);
      if (entityMatch && insightMatch) {
        return t('crawl.messages.extractedKnowledge', `Wyodrębniono ${entityMatch[1]} encji i ${insightMatch[1]} insights`);
      }
    }
    if (message.includes('Finalizing agentic extraction')) {
      return t('crawl.messages.finalizingExtraction', 'Finalizowanie ekstrakcji...');
    }
    if (message.includes('Successfully extracted knowledge')) {
      const match = message.match(/from (\d+) URL/);
      const count = match ? match[1] : '0';
      return t('crawl.messages.extractionComplete', `Pomyślnie wyodrębniono wiedzę z ${count} URLi`);
    }

    // Fallback: return original message
    return message;
  };

  useEffect(() => {
    // Don't poll if already completed or failed
    if (progress.status === 'completed' || progress.status === 'failed') {
      return;
    }

    const fetchProgress = async () => {
      try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(
          `${import.meta.env.VITE_API_URL}/api/v1/crawl/jobs/${jobId}/progress`,
          {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          }
        );

        if (!response.ok) {
          throw new Error(t('crawl.errors.fetchFailed', 'Nie udało się pobrać postępu'));
        }

        const data: CrawlProgress = await response.json();

        // Translate backend messages to current language
        if (data.message) {
          data.message = translateProgressMessage(data.message);
        }

        setProgress(data);

        // Trigger callbacks
        if (data.status === 'completed') {
          onComplete?.();
        } else if (data.status === 'failed' && data.error) {
          onError?.(data.error);
        }
      } catch (err) {
        console.error('Progress poll failed:', err);
        // Continue polling despite errors (backend might be temporarily unavailable)
      }
    };

    // Initial fetch
    fetchProgress();

    // Poll every 2 seconds
    const interval = setInterval(fetchProgress, 2000);

    return () => clearInterval(interval);
  }, [jobId, progress.status, onComplete, onError]);

  // Render status icon
  const renderIcon = () => {
    switch (progress.status) {
      case 'pending':
        return <Clock className="h-4 w-4 text-muted-foreground animate-pulse" />;
      case 'in_progress':
        return <Loader2 className="h-4 w-4 text-primary animate-spin" />;
      case 'completed':
        return <CheckCircle2 className="h-4 w-4 text-green-600 dark:text-green-400" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-destructive" />;
      default:
        return <Clock className="h-4 w-4 text-muted-foreground" />;
    }
  };

  // Render status variant for Alert
  const getAlertVariant = () => {
    if (progress.status === 'completed') return 'default';
    if (progress.status === 'failed') return 'destructive';
    return 'default';
  };

  return (
    <Alert variant={getAlertVariant()} className="mt-4">
      <div className="flex items-start gap-3">
        {renderIcon()}
        <div className="flex-1 space-y-2">
          {/* Progress bar */}
          <div className="space-y-1">
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium">
                {progress.status === 'completed'
                  ? t('crawl.completed')
                  : progress.status === 'failed'
                  ? t('crawl.failed')
                  : progress.status === 'pending'
                  ? t('crawl.pending')
                  : t('crawl.in_progress')}
              </span>
              <span className="text-muted-foreground">
                {progress.progress}%
                {progress.current !== undefined && progress.total !== undefined && (
                  <span className="ml-2">
                    ({progress.current}/{progress.total})
                  </span>
                )}
              </span>
            </div>
            <Progress value={progress.progress} className="h-2" />
          </div>

          {/* Status message */}
          {progress.message && (
            <AlertDescription className="text-sm text-muted-foreground">
              {progress.message}
            </AlertDescription>
          )}

          {/* Error message */}
          {progress.error && (
            <AlertDescription className="text-sm text-destructive font-medium">
              {t('error')}: {progress.error}
            </AlertDescription>
          )}

          {/* Step indicator */}
          {progress.step && progress.status === 'in_progress' && (
            <p className="text-xs text-muted-foreground">
              {t('crawl.step')}: {progress.step}
            </p>
          )}
        </div>
      </div>
    </Alert>
  );
}
