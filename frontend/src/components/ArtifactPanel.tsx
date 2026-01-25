/**
 * Artifact Panel Component
 * Right-side slide-out panel for viewing and managing AI-generated artifacts
 */

import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import ReactMarkdown from 'react-markdown';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  FileText,
  FileEdit,
  Clipboard,
  StickyNote,
  List,
  ArrowLeftRight,
  Lightbulb,
  Sparkles,
  FolderTree,
  Edit,
  Save,
  X,
  RefreshCw,
  Copy,
  Download,
  Trash2,
  Clock,
  Zap,
  FileCode,
  Hash,
} from 'lucide-react';
import type { Artifact, ArtifactType } from '@/types/artifact';
import { ARTIFACT_TYPE_LABELS, ARTIFACT_TYPE_DESCRIPTIONS } from '@/types/artifact';
import { artifactsApi } from '@/lib/api';
import { CategoryTreeArtifact } from '@/components/artifacts/CategoryTreeArtifact';

interface ArtifactPanelProps {
  artifact: Artifact | null;
  isOpen: boolean;
  onClose: () => void;
  onUpdate?: (artifact: Artifact) => void;
  onDelete?: (artifactId: number) => void;
  onRegenerate?: (artifact: Artifact) => void;
}

const ARTIFACT_ICON_MAP: Record<ArtifactType, typeof FileText> = {
  summary: FileText,
  article: FileEdit,
  extract: Clipboard,
  notes: StickyNote,
  outline: List,
  comparison: ArrowLeftRight,
  explanation: Lightbulb,
  category_tree: FolderTree,
  custom: Sparkles,
};

export default function ArtifactPanel({
  artifact,
  isOpen,
  onClose,
  onUpdate,
  onDelete,
  onRegenerate,
}: ArtifactPanelProps) {
  const { t } = useTranslation();
  const [isEditing, setIsEditing] = useState(false);
  const [editedTitle, setEditedTitle] = useState('');
  const [editedContent, setEditedContent] = useState('');
  const [editedType, setEditedType] = useState<ArtifactType>('summary');
  const [isSaving, setIsSaving] = useState(false);
  const [isRegenerating, setIsRegenerating] = useState(false);

  // Initialize edit state when artifact changes
  useEffect(() => {
    if (artifact) {
      setEditedTitle(artifact.title);
      setEditedContent(artifact.content);
      setEditedType(artifact.type);
    }
  }, [artifact]);

  const handleEdit = () => {
    setIsEditing(true);
  };

  const handleCancelEdit = () => {
    if (artifact) {
      setEditedTitle(artifact.title);
      setEditedContent(artifact.content);
      setEditedType(artifact.type);
    }
    setIsEditing(false);
  };

  const handleSave = async () => {
    if (!artifact) return;

    setIsSaving(true);
    try {
      const response = await artifactsApi.update(artifact.id, {
        title: editedTitle,
        content: editedContent,
        type: editedType,
      });

      setIsEditing(false);
      onUpdate?.(response.data);
    } catch (error) {
      console.error('Failed to save artifact:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleRegenerate = async () => {
    if (!artifact || !onRegenerate) return;

    setIsRegenerating(true);
    try {
      const response = await artifactsApi.regenerate(artifact.id);
      onRegenerate(response.data);
    } catch (error) {
      console.error('Failed to regenerate artifact:', error);
    } finally {
      setIsRegenerating(false);
    }
  };

  const handleCopyContent = () => {
    if (artifact) {
      navigator.clipboard.writeText(artifact.content);
    }
  };

  const handleDownload = () => {
    if (!artifact) return;

    const blob = new Blob([artifact.content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${artifact.title.replace(/\s+/g, '_')}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleDelete = async () => {
    if (!artifact || !onDelete) return;

    if (confirm(t('artifacts.confirmDelete', 'Are you sure you want to delete this artifact?'))) {
      try {
        await artifactsApi.delete(artifact.id);
        onDelete(artifact.id);
        onClose();
      } catch (error) {
        console.error('Failed to delete artifact:', error);
      }
    }
  };

  if (!artifact) {
    return (
      <Sheet open={isOpen} onOpenChange={onClose}>
        <SheetContent side="right" className="w-full sm:max-w-2xl overflow-y-auto">
          <SheetHeader>
            <SheetTitle>{t('artifacts.noArtifact', 'No Artifact Selected')}</SheetTitle>
            <SheetDescription>
              {t('artifacts.selectArtifact', 'Select an artifact to view details')}
            </SheetDescription>
          </SheetHeader>
        </SheetContent>
      </Sheet>
    );
  }

  const Icon = ARTIFACT_ICON_MAP[artifact.type];

  return (
    <Sheet open={isOpen} onOpenChange={onClose}>
      <SheetContent side="right" className="w-full sm:max-w-2xl overflow-y-auto">
        <SheetHeader className="space-y-4">
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-center gap-3 flex-1">
              <Icon className="h-6 w-6 text-muted-foreground flex-shrink-0" />
              {isEditing ? (
                <Input
                  value={editedTitle}
                  onChange={(e) => setEditedTitle(e.target.value)}
                  className="font-semibold text-lg"
                  placeholder={t('artifacts.title', 'Artifact title')}
                />
              ) : (
                <SheetTitle className="text-xl">{artifact.title}</SheetTitle>
              )}
            </div>
            <div className="flex items-center gap-2">
              {isEditing ? (
                <>
                  <Button size="sm" variant="outline" onClick={handleCancelEdit}>
                    <X className="h-4 w-4 mr-1" />
                    {t('common.cancel', 'Cancel')}
                  </Button>
                  <Button size="sm" onClick={handleSave} disabled={isSaving}>
                    <Save className="h-4 w-4 mr-1" />
                    {t('common.save', 'Save')}
                  </Button>
                </>
              ) : (
                <Button size="sm" variant="outline" onClick={handleEdit}>
                  <Edit className="h-4 w-4 mr-1" />
                  {t('common.edit', 'Edit')}
                </Button>
              )}
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {isEditing ? (
              <Select value={editedType} onValueChange={(value) => setEditedType(value as ArtifactType)}>
                <SelectTrigger className="w-48">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(ARTIFACT_TYPE_LABELS).map(([type, label]) => (
                    <SelectItem key={type} value={type}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            ) : (
              <Badge variant="secondary" className="text-sm">
                {ARTIFACT_TYPE_LABELS[artifact.type]}
              </Badge>
            )}

            <Badge variant="outline" className="text-sm">
              <Hash className="h-3 w-3 mr-1" />
              v{artifact.version}
            </Badge>

            <Badge variant="outline" className="text-sm">
              <Clock className="h-3 w-3 mr-1" />
              {new Date(artifact.created_at).toLocaleDateString()}
            </Badge>
          </div>

          <SheetDescription>{ARTIFACT_TYPE_DESCRIPTIONS[artifact.type]}</SheetDescription>
        </SheetHeader>

        <div className="mt-6 space-y-6">
          {/* Content Section */}
          {artifact.type === 'category_tree' ? (
            <CategoryTreeArtifact
              projectId={artifact.project_id}
              categoryIds={artifact.metadata?.category_ids}
              sourceUrl={artifact.metadata?.source_url}
              sourceType={artifact.metadata?.source_type}
              metadata={artifact.metadata || undefined}
              onRefresh={undefined}
            />
          ) : (
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center justify-between">
                  <span>{t('artifacts.content', 'Content')}</span>
                  <div className="flex gap-2">
                    <Button size="sm" variant="ghost" onClick={handleCopyContent}>
                      <Copy className="h-4 w-4" />
                    </Button>
                    <Button size="sm" variant="ghost" onClick={handleDownload}>
                      <Download className="h-4 w-4" />
                    </Button>
                  </div>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {isEditing ? (
                  <Textarea
                    value={editedContent}
                    onChange={(e) => setEditedContent(e.target.value)}
                    rows={20}
                    className="font-mono text-sm"
                    placeholder={t('artifacts.contentPlaceholder', 'Artifact content in Markdown format...')}
                  />
                ) : (
                  <div className="prose prose-sm dark:prose-invert max-w-none">
                    <ReactMarkdown>{artifact.content}</ReactMarkdown>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Metadata Section */}
          {artifact.metadata && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <FileCode className="h-4 w-4" />
                  {t('artifacts.metadata', 'Generation Metadata')}
                </CardTitle>
              </CardHeader>
              <CardContent className="grid grid-cols-2 gap-4 text-sm">
                {artifact.metadata.model && (
                  <div>
                    <Label className="text-muted-foreground">{t('artifacts.model', 'Model')}</Label>
                    <p className="font-mono">{artifact.metadata.model}</p>
                  </div>
                )}
                {artifact.metadata.tokens_used && (
                  <div>
                    <Label className="text-muted-foreground">{t('artifacts.tokensUsed', 'Tokens Used')}</Label>
                    <p className="font-mono flex items-center gap-1">
                      <Zap className="h-3 w-3" />
                      {artifact.metadata.tokens_used.toLocaleString()}
                    </p>
                  </div>
                )}
                {artifact.metadata.processing_time_ms && (
                  <div>
                    <Label className="text-muted-foreground">{t('artifacts.processingTime', 'Processing Time')}</Label>
                    <p className="font-mono">
                      {artifact.metadata.processing_time_ms.toFixed(0)}ms
                    </p>
                  </div>
                )}
                {artifact.metadata.chunks_retrieved && (
                  <div>
                    <Label className="text-muted-foreground">{t('artifacts.chunksRetrieved', 'Chunks Retrieved')}</Label>
                    <p className="font-mono">{artifact.metadata.chunks_retrieved}</p>
                  </div>
                )}
                {artifact.metadata.source_documents && artifact.metadata.source_documents.length > 0 && (
                  <div className="col-span-2">
                    <Label className="text-muted-foreground">{t('artifacts.sources', 'Source Documents')}</Label>
                    <div className="mt-1 flex flex-wrap gap-1">
                      {artifact.metadata.source_documents.map((doc, idx) => (
                        <Badge key={idx} variant="outline" className="text-xs">
                          {doc}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Actions Section */}
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" onClick={handleRegenerate} disabled={isRegenerating}>
              <RefreshCw className={`h-4 w-4 mr-2 ${isRegenerating ? 'animate-spin' : ''}`} />
              {t('artifacts.regenerate', 'Regenerate')}
            </Button>
            <Button variant="destructive" onClick={handleDelete}>
              <Trash2 className="h-4 w-4 mr-2" />
              {t('common.delete', 'Delete')}
            </Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
