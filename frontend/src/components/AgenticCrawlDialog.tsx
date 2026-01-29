/**
 * KnowledgeTree - Agentic Crawl Dialog
 *
 * Dialog for initiating agentic web crawling with custom AI extraction prompts.
 * Features intelligent engine selection and multi-URL support.
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Bot,
  Plus,
  X,
  Sparkles,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Globe,
  Zap
} from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface AgenticCrawlDialogProps {
  projectId: number;
  onSuccess?: (jobId: number) => void;
}

interface CrawlResult {
  success: boolean;
  job_id?: number;
  message?: string;
  error?: string;
}

export function AgenticCrawlDialog({ projectId, onSuccess }: AgenticCrawlDialogProps) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [urls, setUrls] = useState<string[]>(['']);
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<CrawlResult | null>(null);

  const handleAddUrl = () => {
    if (urls.length < 20) {
      setUrls([...urls, '']);
    }
  };

  const handleRemoveUrl = (index: number) => {
    const newUrls = urls.filter((_, i) => i !== index);
    setUrls(newUrls.length === 0 ? [''] : newUrls);
  };

  const handleUrlChange = (index: number, value: string) => {
    const newUrls = [...urls];
    newUrls[index] = value;
    setUrls(newUrls);
  };

  const handleSubmit = async () => {
    // Validation
    const validUrls = urls.filter(url => url.trim());
    if (validUrls.length === 0) {
      setError(t('documents.agenticCrawl.errorNoUrls', 'Dodaj przynajmniej jeden URL'));
      return;
    }

    if (!prompt.trim() || prompt.trim().length < 10) {
      setError(t('documents.agenticCrawl.errorPromptTooShort', 'Prompt musi mieć minimum 10 znaków'));
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await fetch('http://localhost:8765/api/v1/crawl/agentic', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          urls: validUrls,
          agent_prompt: prompt.trim(),
          project_id: projectId
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Błąd API');
      }

      const data: CrawlResult = await response.json();
      setResult(data);

      if (data.success && data.job_id && onSuccess) {
        setTimeout(() => {
          onSuccess(data.job_id!);
          handleClose();
        }, 2000);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : t('common.error', 'Wystąpił błąd'));
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setOpen(false);
    setUrls(['']);
    setPrompt('');
    setError('');
    setResult(null);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" className="gap-2">
          <Bot className="h-4 w-4" />
          <span>{t('documents.agenticCrawl.title', 'Crawling Agentowy')}</span>
          <Badge variant="secondary" className="ml-1 gap-1">
            <Sparkles className="h-3 w-3" />
            AI
          </Badge>
        </Button>
      </DialogTrigger>

      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Bot className="h-5 w-5" />
            {t('documents.agenticCrawl.title', 'Crawling Agentowy z AI')}
          </DialogTitle>
          <DialogDescription>
            {t(
              'documents.agenticCrawl.description',
              'Podaj URLe i instrukcję dla AI - system automatycznie wybierze najlepszy silnik crawlingu i wyciągnie strukturalne informacje.'
            )}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* URLs Section */}
          <div className="space-y-2">
            <Label className="flex items-center gap-2">
              <Globe className="h-4 w-4" />
              {t('documents.agenticCrawl.urls', 'URLe do przetworzenia')}
              <span className="text-xs text-muted-foreground">
                ({urls.filter(u => u.trim()).length}/20)
              </span>
            </Label>

            <div className="space-y-2 max-h-60 overflow-y-auto">
              {urls.map((url, index) => (
                <div key={index} className="flex gap-2">
                  <Input
                    placeholder={t(
                      'documents.agenticCrawl.urlPlaceholder',
                      'https://example.com'
                    )}
                    value={url}
                    onChange={(e) => handleUrlChange(index, e.target.value)}
                    disabled={loading}
                  />
                  {urls.length > 1 && (
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleRemoveUrl(index)}
                      disabled={loading}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              ))}
            </div>

            {urls.length < 20 && (
              <Button
                variant="outline"
                size="sm"
                className="w-full gap-2"
                onClick={handleAddUrl}
                disabled={loading}
              >
                <Plus className="h-4 w-4" />
                {t('documents.agenticCrawl.addUrl', 'Dodaj URL')}
              </Button>
            )}
          </div>

          {/* Prompt Section */}
          <div className="space-y-2">
            <Label className="flex items-center gap-2">
              <Sparkles className="h-4 w-4" />
              {t('documents.agenticCrawl.prompt', 'Instrukcja ekstrakcji (AI prompt)')}
            </Label>
            <Textarea
              placeholder={t(
                'documents.agenticCrawl.promptPlaceholder',
                'np. "wyciągnij wszystkie firmy z nazwą, adresem i danymi kontaktowymi" lub "znajdź wszystkie informacje o metodykach konserwacji drewna"'
              )}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              disabled={loading}
              rows={4}
              className="resize-none"
            />
            <p className="text-xs text-muted-foreground">
              {prompt.length}/1000 {t('documents.agenticCrawl.characters', 'znaków')}
            </p>
          </div>

          {/* Engine Info */}
          <Alert>
            <Zap className="h-4 w-4" />
            <AlertDescription className="text-xs">
              {t(
                'documents.agenticCrawl.engineInfo',
                'System automatycznie wybierze optymalny silnik crawlingu (HTTP, Playwright lub Firecrawl) na podstawie analizy URLi i promptu.'
              )}
            </AlertDescription>
          </Alert>

          {/* Error Display */}
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Success Display */}
          {result?.success && (
            <Alert className="border-green-200 bg-green-50 dark:bg-green-950">
              <CheckCircle2 className="h-4 w-4 text-green-600" />
              <AlertDescription className="text-green-800 dark:text-green-200">
                {t('documents.agenticCrawl.success', 'Zadanie utworzone! Job ID: {{jobId}}', {
                  jobId: result.job_id
                })}
              </AlertDescription>
            </Alert>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose} disabled={loading}>
            {t('common.cancel', 'Anuluj')}
          </Button>
          <Button onClick={handleSubmit} disabled={loading} className="gap-2">
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                {t('documents.agenticCrawl.processing', 'Przetwarzanie...')}
              </>
            ) : (
              <>
                <Bot className="h-4 w-4" />
                {t('documents.agenticCrawl.start', 'Rozpocznij Crawling')}
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
