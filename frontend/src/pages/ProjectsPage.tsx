/**
 * KnowledgeTree Projects Page
 * Manage knowledge base projects with CRUD operations
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { projectsApi, exportApi } from '@/lib/api';
import { downloadBlob } from '@/lib/download';
import type { Project } from '@/types/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
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
import { CategoryTree } from '@/components/categories';
import { Loader2, Plus, Edit, Trash2, FileText, FolderTree, Download } from 'lucide-react';

export function ProjectsPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Create dialog state
  const [createOpen, setCreateOpen] = useState(false);
  const [createName, setCreateName] = useState('');
  const [createDescription, setCreateDescription] = useState('');
  const [createLoading, setCreateLoading] = useState(false);

  // Edit dialog state
  const [editOpen, setEditOpen] = useState(false);
  const [editProject, setEditProject] = useState<Project | null>(null);
  const [editName, setEditName] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [editLoading, setEditLoading] = useState(false);

  // Delete dialog state
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleteProject, setDeleteProject] = useState<Project | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  // Categories dialog state
  const [categoriesOpen, setCategoriesOpen] = useState(false);
  const [categoriesProject, setCategoriesProject] = useState<Project | null>(null);

  // Load projects
  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await projectsApi.list();
      const projectsData = response.data.projects || response.data || [];
      setProjects(projectsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('projects.errors.loadFailed'));
    } finally {
      setLoading(false);
    }
  };

  // Create project
  const handleCreate = async () => {
    if (!createName.trim()) return;

    try {
      setCreateLoading(true);
      await projectsApi.create({
        name: createName.trim(),
        description: createDescription.trim() || undefined,
      });

      // Reset form and close dialog
      setCreateName('');
      setCreateDescription('');
      setCreateOpen(false);

      // Reload projects
      await loadProjects();
    } catch (err) {
      setError(err instanceof Error ? err.message : t('projects.create.error'));
    } finally {
      setCreateLoading(false);
    }
  };

  // Open edit dialog
  const openEditDialog = (project: Project) => {
    setEditProject(project);
    setEditName(project.name);
    setEditDescription(project.description || '');
    setEditOpen(true);
  };

  // Update project
  const handleEdit = async () => {
    if (!editProject || !editName.trim()) return;

    try {
      setEditLoading(true);
      await projectsApi.update(editProject.id, {
        name: editName.trim(),
        description: editDescription.trim() || undefined,
      });

      // Close dialog
      setEditOpen(false);

      // Reload projects
      await loadProjects();
    } catch (err) {
      setError(err instanceof Error ? err.message : t('projects.edit.error'));
    } finally {
      setEditLoading(false);
    }
  };

  // Open delete dialog
  const openDeleteDialog = (project: Project) => {
    setDeleteProject(project);
    setDeleteOpen(true);
  };

  // Open categories dialog
  const openCategoriesDialog = (project: Project) => {
    setCategoriesProject(project);
    setCategoriesOpen(true);
  };

  // Delete project
  const handleDelete = async () => {
    if (!deleteProject) return;

    try {
      setDeleteLoading(true);
      await projectsApi.delete(deleteProject.id);

      // Close dialog
      setDeleteOpen(false);

      // Reload projects
      await loadProjects();
    } catch (err) {
      setError(err instanceof Error ? err.message : t('projects.delete.error'));
    } finally {
      setDeleteLoading(false);
    }
  };

  // Format date
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('pl-PL', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  // Export project as JSON
  const handleExportProject = async (project: Project) => {
    try {
      const response = await exportApi.exportProjectJSON(project.id);
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
      const filename = `knowledgetree_project_${project.name}_${timestamp}.json`;
      downloadBlob(response.data, filename);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('projects.errors.exportFailed'));
    }
  };

  return (
    <div className="space-y-6">
      {/* Header with Create Button */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-neutral-900 dark:text-neutral-50">
            {t('projects.title')}
          </h2>
          <p className="text-neutral-600 dark:text-neutral-400 mt-2">
            {t('projects.description')}
          </p>
        </div>

        {/* Create Project Dialog */}
        <Dialog open={createOpen} onOpenChange={setCreateOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              {t('projects.createNew')}
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{t('projects.create.title')}</DialogTitle>
              <DialogDescription>{t('projects.create.description')}</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="create-name">{t('projects.create.nameLabel')}</Label>
                <Input
                  id="create-name"
                  value={createName}
                  onChange={(e) => setCreateName(e.target.value)}
                  placeholder={t('projects.create.namePlaceholder')}
                  disabled={createLoading}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="create-description">{t('projects.create.descriptionLabel')}</Label>
                <Textarea
                  id="create-description"
                  value={createDescription}
                  onChange={(e) => setCreateDescription(e.target.value)}
                  placeholder={t('projects.create.descriptionPlaceholder')}
                  disabled={createLoading}
                  rows={3}
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setCreateOpen(false)}
                disabled={createLoading}
              >
                {t('common.cancel')}
              </Button>
              <Button onClick={handleCreate} disabled={createLoading || !createName.trim()}>
                {createLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {createLoading ? t('projects.create.creating') : t('projects.create.submit')}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-4 bg-error-50 dark:bg-error-900/20 border border-error-200 dark:border-error-800 rounded text-error-700 dark:text-error-400">
          {error}
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
        </div>
      )}

      {/* Empty State */}
      {!loading && projects.length === 0 && (
        <Card className="text-center py-12">
          <CardContent>
            <div className="mx-auto w-12 h-12 rounded-full bg-neutral-100 dark:bg-neutral-800 flex items-center justify-center mb-4">
              <FileText className="h-6 w-6 text-neutral-400" />
            </div>
            <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-50 mb-2">
              {t('projects.noProjects')}
            </h3>
            <p className="text-neutral-600 dark:text-neutral-400 mb-4">
              {t('projects.noProjectsDescription')}
            </p>
            <Button onClick={() => setCreateOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              {t('projects.createNew')}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Projects Grid */}
      {!loading && projects.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((project) => (
            <Card key={project.id}>
              <CardHeader>
                <CardTitle className="text-xl">{project.name}</CardTitle>
                {project.description && (
                  <CardDescription>{project.description}</CardDescription>
                )}
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-neutral-600 dark:text-neutral-400 flex items-center">
                    <FileText className="mr-1 h-4 w-4" />
                    {t('projects.stats.documents')}
                  </span>
                  <span className="font-medium text-neutral-900 dark:text-neutral-50">
                    {project.document_count || 0}
                  </span>
                </div>
                {/* Conversations info - not available in current Project type */}
                {/*
                <div className="flex items-center justify-between text-sm">
                  <span className="text-neutral-600 dark:text-neutral-400 flex items-center">
                    <MessageSquare className="mr-1 h-4 w-4" />
                    {t('projects.stats.conversations')}
                  </span>
                  <span className="font-medium text-neutral-900 dark:text-neutral-50">
                    -
                  </span>
                </div>
                */}
                <div className="pt-2 border-t border-neutral-200 dark:border-neutral-800">
                  <p className="text-xs text-neutral-500 dark:text-neutral-600">
                    {t('projects.stats.createdAt')}: {formatDate(project.created_at)}
                  </p>
                </div>
              </CardContent>
              <CardFooter className="flex flex-col gap-2">
                <div className="flex gap-2 w-full">
                  <Button
                    variant="default"
                    size="sm"
                    className="flex-1"
                    onClick={() => navigate('/documents')}
                  >
                    <FileText className="mr-2 h-4 w-4" />
                    {t('projects.viewDocuments', 'Documents')}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1"
                    onClick={() => openCategoriesDialog(project)}
                  >
                    <FolderTree className="mr-2 h-4 w-4" />
                    {t('projects.categories', 'Categories')}
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2 w-full">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => openEditDialog(project)}
                  >
                    <Edit className="mr-2 h-4 w-4" />
                    {t('common.edit')}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleExportProject(project)}
                  >
                    <Download className="mr-2 h-4 w-4" />
                    {t('common.export', 'Export')}
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => openDeleteDialog(project)}
                  >
                    <Trash2 className="mr-2 h-4 w-4" />
                    {t('common.delete')}
                  </Button>
                </div>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}

      {/* Edit Project Dialog */}
      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('projects.edit.title')}</DialogTitle>
            <DialogDescription>{t('projects.edit.description')}</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="edit-name">{t('projects.create.nameLabel')}</Label>
              <Input
                id="edit-name"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                placeholder={t('projects.create.namePlaceholder')}
                disabled={editLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-description">{t('projects.create.descriptionLabel')}</Label>
              <Textarea
                id="edit-description"
                value={editDescription}
                onChange={(e) => setEditDescription(e.target.value)}
                placeholder={t('projects.create.descriptionPlaceholder')}
                disabled={editLoading}
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setEditOpen(false)}
              disabled={editLoading}
            >
              {t('common.cancel')}
            </Button>
            <Button onClick={handleEdit} disabled={editLoading || !editName.trim()}>
              {editLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {editLoading ? t('projects.edit.updating') : t('projects.edit.submit')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Categories Dialog */}
      <Dialog open={categoriesOpen} onOpenChange={setCategoriesOpen}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {t('categories.manage', 'Manage Categories')}
              {categoriesProject && ` - ${categoriesProject.name}`}
            </DialogTitle>
            <DialogDescription>
              {t('categories.manageDescription', 'Organize your documents with a hierarchical category structure')}
            </DialogDescription>
          </DialogHeader>
          {categoriesProject && (
            <CategoryTree projectId={categoriesProject.id} />
          )}
        </DialogContent>
      </Dialog>

      {/* Delete Project Dialog */}
      <AlertDialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t('projects.delete.title')}</AlertDialogTitle>
            <AlertDialogDescription className="space-y-2">
              <p>{t('projects.delete.description')}</p>
              {deleteProject && (
                <p className="font-medium text-neutral-900 dark:text-neutral-50">
                  {deleteProject.name}
                </p>
              )}
              <p className="text-error-600 dark:text-error-400">
                {t('projects.delete.warning')}
              </p>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleteLoading}>
              {t('projects.delete.cancel')}
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={deleteLoading}
              className="bg-error-600 hover:bg-error-700 dark:bg-error-700 dark:hover:bg-error-800"
            >
              {deleteLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {deleteLoading ? t('projects.delete.deleting') : t('projects.delete.confirm')}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
