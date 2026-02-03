/**
 * ContentTemplatesDialog - Content Templates Management
 *
 * Features:
 * - Browse available templates
 * - Create new templates
 * - Use templates to populate content
 * - Template preview
 */

import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  FileText,
  Plus,
  Search,
  Loader2,
  X,
} from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';
import { contentWorkbenchApi } from '@/lib/api/contentApi';
import type { ContentTemplate, TemplateType } from '@/types/content';

interface ContentTemplatesDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onTemplateSelect?: (template: ContentTemplate) => void;
}

export function ContentTemplatesDialog({
  isOpen,
  onClose,
  onTemplateSelect,
}: ContentTemplatesDialogProps) {
  const { t } = useTranslation();
  const { toast } = useToast();

  const [templates, setTemplates] = useState<ContentTemplate[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState<TemplateType | 'all'>('all');
  const [activeTab, setActiveTab] = useState<'browse' | 'create'>('browse');

  // Create template form state
  const [templateName, setTemplateName] = useState('');
  const [templateDescription, setTemplateDescription] = useState('');
  const [templateType, setTemplateType] = useState<TemplateType>('article');
  const [templateContent, setTemplateContent] = useState('');
  const [isPublic, setIsPublic] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadTemplates();
    }
  }, [isOpen]);

  const loadTemplates = async () => {
    setIsLoading(true);
    try {
      const response = await contentWorkbenchApi.listTemplates();
      setTemplates(response.data);
    } catch (error) {
      console.error('Failed to load templates:', error);
      toast({
        title: t('contentWorkbench.errors.templatesFailed'),
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateTemplate = async () => {
    if (!templateName.trim()) {
      toast({
        title: t('contentWorkbench.templates.nameRequired', 'Name is required'),
        variant: 'destructive',
      });
      return;
    }

    setIsCreating(true);
    try {
      const response = await contentWorkbenchApi.createTemplate({
        name: templateName,
        description: templateDescription || undefined,
        template_type: templateType,
        sections: [],  // TODO: Parse templateContent into sections array
        is_public: isPublic,
      });

      setTemplates([response.data, ...templates]);
      toast({
        title: t('contentWorkbench.templates.createSuccess'),
      });

      // Reset form
      setTemplateName('');
      setTemplateDescription('');
      setTemplateContent('');
      setIsPublic(false);
      setActiveTab('browse');
    } catch (error) {
      console.error('Failed to create template:', error);
      toast({
        title: t('contentWorkbench.templates.createError'),
        variant: 'destructive',
      });
    } finally {
      setIsCreating(false);
    }
  };

  const handleSelectTemplate = (template: ContentTemplate) => {
    if (onTemplateSelect) {
      onTemplateSelect(template);
    }
    toast({
      title: t('contentWorkbench.templates.applied', 'Template applied'),
    });
    onClose();
  };

  const filteredTemplates = templates.filter((template) => {
    const matchesSearch =
      searchQuery === '' ||
      template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      template.description?.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesType =
      selectedType === 'all' || template.template_type === selectedType;

    return matchesSearch && matchesType;
  });

  const getTypeVariant = (type: TemplateType) => {
    switch (type) {
      case 'how_to':
        return 'default';
      case 'faq':
        return 'secondary';
      case 'tutorial':
        return 'outline';
      case 'article':
        return 'default';
      case 'reference':
        return 'secondary';
      default:
        return 'outline';
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl h-[80vh] flex flex-col p-0">
        <DialogHeader className="px-6 py-4 border-b">
          <div className="flex items-center justify-between">
            <div>
              <DialogTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                {t('contentWorkbench.templates.title')}
              </DialogTitle>
              <DialogDescription className="mt-1">
                {t('contentWorkbench.templates.description')}
              </DialogDescription>
            </div>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as any)} className="flex-1 flex flex-col">
          <TabsList className="mx-6 mt-4">
            <TabsTrigger value="browse">
              {t('contentWorkbench.templates.browse', 'Browse Templates')}
            </TabsTrigger>
            <TabsTrigger value="create">
              <Plus className="h-4 w-4 mr-2" />
              {t('contentWorkbench.templates.create')}
            </TabsTrigger>
          </TabsList>

          {/* Browse Templates Tab */}
          <TabsContent value="browse" className="flex-1 m-0 px-6 pb-6 flex flex-col">
            {/* Search and filter */}
            <div className="flex gap-2 mb-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder={t('common.search')}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9"
                />
              </div>
              <Select
                value={selectedType}
                onValueChange={(value) => setSelectedType(value as TemplateType | 'all')}
              >
                <SelectTrigger className="w-[200px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">
                    {t('contentWorkbench.templates.allTypes', 'All Types')}
                  </SelectItem>
                  <SelectItem value="how_to">
                    {t('contentWorkbench.templates.types.how_to')}
                  </SelectItem>
                  <SelectItem value="faq">
                    {t('contentWorkbench.templates.types.faq')}
                  </SelectItem>
                  <SelectItem value="tutorial">
                    {t('contentWorkbench.templates.types.tutorial')}
                  </SelectItem>
                  <SelectItem value="article">
                    {t('contentWorkbench.templates.types.article')}
                  </SelectItem>
                  <SelectItem value="reference">
                    {t('contentWorkbench.templates.types.reference')}
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Templates list */}
            <ScrollArea className="flex-1">
              {isLoading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
              ) : filteredTemplates.length === 0 ? (
                <div className="text-center py-12">
                  <FileText className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <p className="text-sm text-muted-foreground mb-2">
                    {t('contentWorkbench.templates.noTemplates')}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {t('contentWorkbench.templates.noTemplatesDescription')}
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-2 gap-4">
                  {filteredTemplates.map((template) => (
                    <div
                      key={template.id}
                      className="border rounded-lg p-4 space-y-3 hover:bg-accent/50 transition-colors cursor-pointer"
                      onClick={() => handleSelectTemplate(template)}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1">
                          <h4 className="font-medium text-sm mb-1">
                            {template.name}
                          </h4>
                          {template.description && (
                            <p className="text-xs text-muted-foreground line-clamp-2">
                              {template.description}
                            </p>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <Badge variant={getTypeVariant(template.template_type)} className="text-xs">
                          {t(`contentWorkbench.templates.types.${template.template_type}`)}
                        </Badge>
                        {template.is_public && (
                          <Badge variant="outline" className="text-xs">
                            {t('contentWorkbench.templates.public', 'Public')}
                          </Badge>
                        )}
                      </div>

                      {template.structure && template.structure.sections && (
                        <div className="bg-muted/30 p-2 rounded text-xs font-mono text-muted-foreground line-clamp-3">
                          {t('contentWorkbench.templates.structure', 'Template Structure')}: {template.structure.sections.length} {t('contentWorkbench.templates.sections', 'sections')}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </TabsContent>

          {/* Create Template Tab */}
          <TabsContent value="create" className="flex-1 m-0 px-6 pb-6">
            <ScrollArea className="h-full">
              <div className="space-y-4 pr-4">
                <div className="space-y-2">
                  <Label htmlFor="template-name">
                    {t('contentWorkbench.templates.templateName')}
                  </Label>
                  <Input
                    id="template-name"
                    value={templateName}
                    onChange={(e) => setTemplateName(e.target.value)}
                    placeholder="np. Poradnik krok po kroku"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="template-description">
                    {t('contentWorkbench.templates.templateDescription')}
                  </Label>
                  <Textarea
                    id="template-description"
                    value={templateDescription}
                    onChange={(e) => setTemplateDescription(e.target.value)}
                    placeholder="Opcjonalny opis szablonu"
                    rows={2}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="template-type">
                    {t('contentWorkbench.templates.templateType')}
                  </Label>
                  <Select
                    value={templateType}
                    onValueChange={(value) => setTemplateType(value as TemplateType)}
                  >
                    <SelectTrigger id="template-type">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="how_to">
                        {t('contentWorkbench.templates.types.how_to')}
                      </SelectItem>
                      <SelectItem value="faq">
                        {t('contentWorkbench.templates.types.faq')}
                      </SelectItem>
                      <SelectItem value="tutorial">
                        {t('contentWorkbench.templates.types.tutorial')}
                      </SelectItem>
                      <SelectItem value="article">
                        {t('contentWorkbench.templates.types.article')}
                      </SelectItem>
                      <SelectItem value="reference">
                        {t('contentWorkbench.templates.types.reference')}
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="template-content">
                    {t('contentWorkbench.templates.structure', 'Template Structure')}
                  </Label>
                  <Textarea
                    id="template-content"
                    value={templateContent}
                    onChange={(e) => setTemplateContent(e.target.value)}
                    placeholder="# Tytuł&#10;&#10;## Wprowadzenie&#10;...&#10;&#10;## Podsumowanie"
                    rows={12}
                    className="font-mono text-sm"
                  />
                </div>

                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="is-public"
                    checked={isPublic}
                    onChange={(e) => setIsPublic(e.target.checked)}
                    className="rounded"
                  />
                  <Label htmlFor="is-public" className="cursor-pointer">
                    {t('contentWorkbench.templates.isPublic')}
                  </Label>
                </div>
              </div>
            </ScrollArea>

            <DialogFooter className="mt-4">
              <Button variant="outline" onClick={() => setActiveTab('browse')}>
                {t('common.cancel')}
              </Button>
              <Button onClick={handleCreateTemplate} disabled={isCreating}>
                {isCreating ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    {t('contentWorkbench.templates.creating')}
                  </>
                ) : (
                  <>
                    <Plus className="h-4 w-4 mr-2" />
                    {t('contentWorkbench.templates.save')}
                  </>
                )}
              </Button>
            </DialogFooter>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
