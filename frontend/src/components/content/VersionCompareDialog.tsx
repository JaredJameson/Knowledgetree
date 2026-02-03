/**
 * VersionCompareDialog - Version Comparison Dialog
 *
 * Features:
 * - Side-by-side version comparison
 * - Diff highlighting
 * - Version metadata display
 * - Restore from comparison
 */

import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { X, GitCompare, Loader2 } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';
import { contentWorkbenchApi } from '@/lib/api/contentApi';
import type { ContentVersion } from '@/types/content';
import { cn } from '@/lib/utils';

interface VersionCompareDialogProps {
  categoryId: number;
  versionIdA: number;
  versionIdB: number;
  isOpen: boolean;
  onClose: () => void;
}

export function VersionCompareDialog({
  categoryId,
  versionIdA,
  versionIdB,
  isOpen,
  onClose,
}: VersionCompareDialogProps) {
  const { t } = useTranslation();
  const { toast } = useToast();

  const [versionA, setVersionA] = useState<ContentVersion | null>(null);
  const [versionB, setVersionB] = useState<ContentVersion | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [diffLines, setDiffLines] = useState<Array<{
    type: 'added' | 'removed' | 'unchanged';
    content: string;
    lineNumber: number;
  }>>([]);

  useEffect(() => {
    if (isOpen) {
      loadVersions();
    }
  }, [isOpen, versionIdA, versionIdB]);

  const loadVersions = async () => {
    setIsLoading(true);
    try {
      // Load both versions
      const [responseA, responseB] = await Promise.all([
        contentWorkbenchApi.getVersion(categoryId, versionIdA),
        contentWorkbenchApi.getVersion(categoryId, versionIdB),
      ]);

      setVersionA(responseA.data);
      setVersionB(responseB.data);

      // Calculate simple diff
      const diff = calculateSimpleDiff(
        responseA.data.content,
        responseB.data.content
      );
      setDiffLines(diff);
    } catch (error) {
      console.error('Failed to load versions:', error);
      toast({
        title: t('contentWorkbench.versions.compareError'),
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const calculateSimpleDiff = (textA: string, textB: string) => {
    const linesA = textA.split('\n');
    const linesB = textB.split('\n');
    const diff: Array<{
      type: 'added' | 'removed' | 'unchanged';
      content: string;
      lineNumber: number;
    }> = [];

    // Simple line-by-line comparison
    const maxLength = Math.max(linesA.length, linesB.length);
    let lineNumber = 0;

    for (let i = 0; i < maxLength; i++) {
      const lineA = linesA[i] || '';
      const lineB = linesB[i] || '';

      if (lineA === lineB) {
        diff.push({
          type: 'unchanged',
          content: lineA,
          lineNumber: ++lineNumber,
        });
      } else {
        if (lineA && !linesB[i]) {
          diff.push({
            type: 'removed',
            content: lineA,
            lineNumber: ++lineNumber,
          });
        } else if (!linesA[i] && lineB) {
          diff.push({
            type: 'added',
            content: lineB,
            lineNumber: ++lineNumber,
          });
        } else {
          // Both lines exist but differ
          diff.push({
            type: 'removed',
            content: lineA,
            lineNumber: ++lineNumber,
          });
          diff.push({
            type: 'added',
            content: lineB,
            lineNumber: lineNumber,
          });
        }
      }
    }

    return diff;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('pl-PL', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-6xl h-[80vh] flex flex-col p-0">
        <DialogHeader className="px-6 py-4 border-b">
          <div className="flex items-center justify-between">
            <div>
              <DialogTitle className="flex items-center gap-2">
                <GitCompare className="h-5 w-5" />
                {t('contentWorkbench.versions.compareVersions')}
              </DialogTitle>
              <DialogDescription className="mt-1">
                {t('contentWorkbench.versions.differences')}
              </DialogDescription>
            </div>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </DialogHeader>

        {isLoading ? (
          <div className="flex items-center justify-center flex-1">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <Tabs defaultValue="diff" className="flex-1 flex flex-col">
            <TabsList className="mx-6 mt-4">
              <TabsTrigger value="diff">
                {t('contentWorkbench.versions.differences')}
              </TabsTrigger>
              <TabsTrigger value="side-by-side">
                {t('contentWorkbench.versions.sideBySide', 'Side by Side')}
              </TabsTrigger>
            </TabsList>

            {/* Diff view */}
            <TabsContent value="diff" className="flex-1 m-0 px-6 pb-6">
              <ScrollArea className="h-full border rounded-md">
                <div className="p-4 font-mono text-xs">
                  {diffLines.map((line, index) => (
                    <div
                      key={index}
                      className={cn(
                        'px-2 py-0.5 whitespace-pre-wrap',
                        line.type === 'added' && 'bg-green-100 dark:bg-green-950 text-green-900 dark:text-green-100',
                        line.type === 'removed' && 'bg-red-100 dark:bg-red-950 text-red-900 dark:text-red-100',
                        line.type === 'unchanged' && 'text-muted-foreground'
                      )}
                    >
                      <span className="inline-block w-8 text-right mr-4 select-none opacity-50">
                        {line.lineNumber}
                      </span>
                      <span className="inline-block w-4 mr-2 font-bold select-none">
                        {line.type === 'added' && '+'}
                        {line.type === 'removed' && '-'}
                        {line.type === 'unchanged' && ' '}
                      </span>
                      {line.content || ' '}
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </TabsContent>

            {/* Side-by-side view */}
            <TabsContent value="side-by-side" className="flex-1 m-0 px-6 pb-6">
              <div className="grid grid-cols-2 gap-4 h-full">
                {/* Version A */}
                <div className="border rounded-md flex flex-col">
                  <div className="border-b p-3 bg-muted/30">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium">
                        {t('contentWorkbench.versions.version')} {versionA?.version_number}
                      </span>
                      <Badge variant="outline">
                        {t('contentWorkbench.versions.versionA')}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {versionA && formatDate(versionA.created_at)}
                    </p>
                  </div>
                  <ScrollArea className="flex-1">
                    <div className="p-4 text-sm whitespace-pre-wrap font-mono">
                      {versionA?.content}
                    </div>
                  </ScrollArea>
                </div>

                {/* Version B */}
                <div className="border rounded-md flex flex-col">
                  <div className="border-b p-3 bg-muted/30">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium">
                        {t('contentWorkbench.versions.version')} {versionB?.version_number}
                      </span>
                      <Badge variant="outline">
                        {t('contentWorkbench.versions.versionB')}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {versionB && formatDate(versionB.created_at)}
                    </p>
                  </div>
                  <ScrollArea className="flex-1">
                    <div className="p-4 text-sm whitespace-pre-wrap font-mono">
                      {versionB?.content}
                    </div>
                  </ScrollArea>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        )}
      </DialogContent>
    </Dialog>
  );
}
