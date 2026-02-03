/**
 * VersionHistoryPanel - Version History Management
 *
 * Features:
 * - List all versions for a category
 * - Compare versions (diff view)
 * - Restore previous versions
 * - Version metadata display
 */

import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { History, RotateCcw, GitCompare, Loader2, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { useToast } from '@/hooks/use-toast';
import { contentWorkbenchApi } from '@/lib/api/contentApi';
import type { ContentVersion } from '@/types/content';
import { VersionCompareDialog } from './VersionCompareDialog';
import { cn } from '@/lib/utils';

interface VersionHistoryPanelProps {
  categoryId: number;
  onVersionRestore?: (version: ContentVersion) => void;
  className?: string;
}

export function VersionHistoryPanel({
  categoryId,
  onVersionRestore,
  className,
}: VersionHistoryPanelProps) {
  const { t } = useTranslation();
  const { toast } = useToast();

  const [versions, setVersions] = useState<ContentVersion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isRestoring, setIsRestoring] = useState(false);
  const [restoreVersionId, setRestoreVersionId] = useState<number | null>(null);
  const [showRestoreConfirm, setShowRestoreConfirm] = useState(false);
  const [showCompareDialog, setShowCompareDialog] = useState(false);
  const [compareVersionA, setCompareVersionA] = useState<number | null>(null);
  const [compareVersionB, setCompareVersionB] = useState<number | null>(null);

  useEffect(() => {
    loadVersions();
  }, [categoryId]);

  const loadVersions = async () => {
    setIsLoading(true);
    try {
      const response = await contentWorkbenchApi.listVersions(categoryId);
      setVersions(response.data);
    } catch (error) {
      console.error('Failed to load versions:', error);
      toast({
        title: t('contentWorkbench.errors.versionsFailed'),
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleRestoreClick = (versionId: number) => {
    setRestoreVersionId(versionId);
    setShowRestoreConfirm(true);
  };

  const handleRestoreConfirm = async () => {
    if (!restoreVersionId) return;

    setIsRestoring(true);
    try {
      await contentWorkbenchApi.restoreVersion(
        categoryId,
        { version_number: restoreVersionId, create_new_version: true }
      );

      // Find the restored version
      const restoredVersion = versions.find(v => v.id === restoreVersionId);
      if (restoredVersion && onVersionRestore) {
        onVersionRestore(restoredVersion);
      }

      toast({
        title: t('contentWorkbench.versions.restoreSuccess'),
      });

      // Reload versions to show the new version created from restore
      await loadVersions();
      setShowRestoreConfirm(false);
    } catch (error) {
      console.error('Failed to restore version:', error);
      toast({
        title: t('contentWorkbench.versions.restoreError'),
        variant: 'destructive',
      });
    } finally {
      setIsRestoring(false);
      setRestoreVersionId(null);
    }
  };

  const handleCompareClick = (versionId: number) => {
    if (!compareVersionA) {
      setCompareVersionA(versionId);
    } else if (!compareVersionB) {
      setCompareVersionB(versionId);
      setShowCompareDialog(true);
    } else {
      // Reset and set new first version
      setCompareVersionA(versionId);
      setCompareVersionB(null);
    }
  };

  const handleCompareDialogClose = () => {
    setShowCompareDialog(false);
    setCompareVersionA(null);
    setCompareVersionB(null);
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
    <>
      <div className={className}>
        <div className="space-y-4">
          <div>
            <h3 className="font-semibold text-sm mb-3 flex items-center gap-2">
              <History className="h-4 w-4" />
              {t('contentWorkbench.versions.title')}
            </h3>
            <p className="text-xs text-muted-foreground mb-4">
              {t('contentWorkbench.versions.description')}
            </p>
          </div>

          {/* Version list */}
          <ScrollArea className="h-[400px]">
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : versions.length === 0 ? (
              <div className="text-center py-8 text-sm text-muted-foreground">
                {t('contentWorkbench.versions.noVersions')}
              </div>
            ) : (
              <div className="space-y-3">
                {versions.map((version, index) => (
                  <div
                    key={version.id}
                    className={cn(
                      'border rounded-lg p-3 space-y-2',
                      index === 0 && 'border-primary bg-primary/5',
                      (compareVersionA === version.id || compareVersionB === version.id) &&
                        'border-blue-500 bg-blue-50 dark:bg-blue-950'
                    )}
                  >
                    {/* Version header */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">
                          {t('contentWorkbench.versions.version')} {version.version_number}
                        </span>
                        {index === 0 && (
                          <Badge variant="default" className="text-xs">
                            {t('contentWorkbench.versions.current')}
                          </Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-1">
                        {index !== 0 && (
                          <>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-7 w-7 p-0"
                              onClick={() => handleRestoreClick(version.id)}
                              title={t('contentWorkbench.versions.restore')}
                            >
                              <RotateCcw className="h-3 w-3" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              className={cn(
                                'h-7 w-7 p-0',
                                (compareVersionA === version.id || compareVersionB === version.id) &&
                                  'bg-blue-100 dark:bg-blue-900'
                              )}
                              onClick={() => handleCompareClick(version.id)}
                              title={t('contentWorkbench.versions.compare')}
                            >
                              <GitCompare className="h-3 w-3" />
                            </Button>
                          </>
                        )}
                      </div>
                    </div>

                    {/* Version metadata */}
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <Clock className="h-3 w-3" />
                        {formatDate(version.created_at)}
                      </div>

                      {version.change_summary && (
                        <p className="text-xs text-muted-foreground">
                          {version.change_summary}
                        </p>
                      )}
                    </div>

                    {/* Content preview */}
                    <div className="text-xs text-muted-foreground bg-muted/30 p-2 rounded border">
                      <p className="line-clamp-2">{version.content}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>

          {/* Compare button hint */}
          {compareVersionA && !compareVersionB && (
            <div className="text-xs text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950 p-2 rounded border border-blue-200 dark:border-blue-800">
              {t('contentWorkbench.versions.selectVersionB')}
            </div>
          )}
        </div>
      </div>

      {/* Restore confirmation dialog */}
      <AlertDialog open={showRestoreConfirm} onOpenChange={setShowRestoreConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {t('contentWorkbench.versions.restore')}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {t('contentWorkbench.versions.restoreConfirm')}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>
              {t('common.cancel')}
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleRestoreConfirm}
              disabled={isRestoring}
            >
              {isRestoring ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  {t('contentWorkbench.versions.restoring')}
                </>
              ) : (
                t('contentWorkbench.versions.restore')
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Version comparison dialog */}
      {showCompareDialog && compareVersionA && compareVersionB && (
        <VersionCompareDialog
          categoryId={categoryId}
          versionIdA={compareVersionA}
          versionIdB={compareVersionB}
          isOpen={showCompareDialog}
          onClose={handleCompareDialogClose}
        />
      )}
    </>
  );
}
