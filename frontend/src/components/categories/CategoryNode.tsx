/**
 * CategoryNode Component
 * Individual node in the category tree with actions
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { categoriesApi } from '@/lib/api';
import type { CategoryTreeNode } from '@/types/api';
import { Button } from '@/components/ui/button';
import { CategoryDialog } from './CategoryDialog';
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
import {
  ChevronRight,
  ChevronDown,
  Folder,
  FolderOpen,
  Plus,
  Edit,
  Trash2,
  Loader2,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface CategoryNodeProps {
  category: CategoryTreeNode;
  expanded: boolean;
  selected: boolean;
  onToggleExpand: (categoryId: number) => void;
  onSelect: (category: CategoryTreeNode) => void;
  onCreateChild: (parentId: number) => void;
  onUpdate: () => void;
  onDelete: () => void;
}

export function CategoryNode({
  category,
  expanded,
  selected,
  onToggleExpand,
  onSelect,
  onCreateChild,
  onUpdate,
  onDelete,
}: CategoryNodeProps) {
  const { t } = useTranslation();
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const hasChildren = category.children && category.children.length > 0;

  const handleToggleExpand = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (hasChildren) {
      onToggleExpand(category.id);
    }
  };

  const handleSelect = () => {
    onSelect(category);
  };

  const handleCreateChild = (e: React.MouseEvent) => {
    e.stopPropagation();
    onCreateChild(category.id);
  };

  const handleEdit = (e: React.MouseEvent) => {
    e.stopPropagation();
    setEditDialogOpen(true);
  };

  const handleDeleteClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setDeleteDialogOpen(true);
  };

  const handleDelete = async () => {
    try {
      setDeleteLoading(true);
      await categoriesApi.delete(category.id, true); // cascade delete
      setDeleteDialogOpen(false);
      onDelete();
    } catch (err) {
      console.error('Failed to delete category:', err);
    } finally {
      setDeleteLoading(false);
    }
  };

  const handleCategoryUpdated = () => {
    setEditDialogOpen(false);
    onUpdate();
  };

  return (
    <div>
      {/* Node */}
      <div
        className={cn(
          'group flex items-center gap-1 px-2 py-1.5 rounded-md cursor-pointer hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors',
          selected && 'bg-primary-50 dark:bg-primary-900/20 hover:bg-primary-100 dark:hover:bg-primary-900/30'
        )}
        style={{ paddingLeft: `${category.depth * 20 + 8}px` }}
        onClick={handleSelect}
      >
        {/* Expand/Collapse Button */}
        <button
          onClick={handleToggleExpand}
          className={cn(
            'flex items-center justify-center w-5 h-5 rounded hover:bg-neutral-200 dark:hover:bg-neutral-700',
            !hasChildren && 'invisible'
          )}
        >
          {expanded ? (
            <ChevronDown className="h-4 w-4 text-neutral-600 dark:text-neutral-400" />
          ) : (
            <ChevronRight className="h-4 w-4 text-neutral-600 dark:text-neutral-400" />
          )}
        </button>

        {/* Icon */}
        <div
          className="flex items-center justify-center w-5 h-5"
          style={{ color: category.color }}
        >
          {expanded && hasChildren ? (
            <FolderOpen className="h-4 w-4" />
          ) : (
            <Folder className="h-4 w-4" />
          )}
        </div>

        {/* Name */}
        <span className="flex-1 text-sm font-medium text-neutral-900 dark:text-neutral-50">
          {category.name}
        </span>

        {/* Actions (visible on hover) */}
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <Button
            size="sm"
            variant="ghost"
            onClick={handleCreateChild}
            className="h-6 px-2"
            title={t('categories.createChild', 'Add subcategory')}
          >
            <Plus className="h-3 w-3" />
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={handleEdit}
            className="h-6 px-2"
            title={t('common.edit', 'Edit')}
          >
            <Edit className="h-3 w-3" />
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={handleDeleteClick}
            className="h-6 px-2 text-error-600 hover:text-error-700 hover:bg-error-50 dark:hover:bg-error-900/20"
            title={t('common.delete', 'Delete')}
          >
            <Trash2 className="h-3 w-3" />
          </Button>
        </div>
      </div>

      {/* Children */}
      {expanded && hasChildren && (
        <div>
          {category.children.map((child) => (
            <CategoryNode
              key={child.id}
              category={child}
              expanded={expanded}
              selected={selected}
              onToggleExpand={onToggleExpand}
              onSelect={onSelect}
              onCreateChild={onCreateChild}
              onUpdate={onUpdate}
              onDelete={onDelete}
            />
          ))}
        </div>
      )}

      {/* Edit Dialog */}
      <CategoryDialog
        open={editDialogOpen}
        onOpenChange={setEditDialogOpen}
        projectId={category.project_id}
        category={category}
        onSuccess={handleCategoryUpdated}
      />

      {/* Delete Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {t('categories.delete.title', 'Delete Category')}
            </AlertDialogTitle>
            <AlertDialogDescription className="space-y-2">
              <p>
                {t(
                  'categories.delete.description',
                  'Are you sure you want to delete this category?'
                )}
              </p>
              <p className="font-medium text-neutral-900 dark:text-neutral-50">
                {category.name}
              </p>
              {hasChildren && (
                <p className="text-error-600 dark:text-error-400">
                  {t(
                    'categories.delete.warningChildren',
                    'This will also delete all subcategories.'
                  )}
                </p>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleteLoading}>
              {t('common.cancel', 'Cancel')}
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={deleteLoading}
              className="bg-error-600 hover:bg-error-700 dark:bg-error-700 dark:hover:bg-error-800"
            >
              {deleteLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {deleteLoading
                ? t('categories.delete.deleting', 'Deleting...')
                : t('categories.delete.confirm', 'Delete')}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
