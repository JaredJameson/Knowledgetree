/**
 * CategoryTree Component
 * Hierarchical tree view for categories with expand/collapse
 */

import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { categoriesApi } from '@/lib/api';
import type { CategoryTreeNode } from '@/types/api';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { CategoryNode } from './CategoryNode';
import { CategoryDialog } from './CategoryDialog';
import { Loader2, Plus, FolderTree } from 'lucide-react';

interface CategoryTreeProps {
  projectId: number;
  onCategorySelect?: (category: CategoryTreeNode | null) => void;
  selectedCategoryId?: number | null;
}

export function CategoryTree({
  projectId,
  onCategorySelect,
  selectedCategoryId,
}: CategoryTreeProps) {
  const { t } = useTranslation();
  const [tree, setTree] = useState<CategoryTreeNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expandedIds, setExpandedIds] = useState<Set<number>>(new Set());
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [createParentId, setCreateParentId] = useState<number | null>(null);

  // Load category tree
  useEffect(() => {
    loadTree();
  }, [projectId]);

  const loadTree = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await categoriesApi.getTree(projectId);
      setTree(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load categories');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleExpand = (categoryId: number) => {
    setExpandedIds((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(categoryId)) {
        newSet.delete(categoryId);
      } else {
        newSet.add(categoryId);
      }
      return newSet;
    });
  };

  const handleCreateRoot = () => {
    setCreateParentId(null);
    setCreateDialogOpen(true);
  };

  const handleCreateChild = (parentId: number) => {
    setCreateParentId(parentId);
    setCreateDialogOpen(true);
  };

  const handleCategoryCreated = () => {
    loadTree();
    setCreateDialogOpen(false);
  };

  const handleCategoryUpdated = () => {
    loadTree();
  };

  const handleCategoryDeleted = () => {
    loadTree();
  };

  const handleCategorySelect = (category: CategoryTreeNode) => {
    if (onCategorySelect) {
      onCategorySelect(category);
    }
  };

  if (loading) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-primary-600" />
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="p-6">
        <div className="text-center text-error-600 dark:text-error-400">
          {error}
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FolderTree className="h-5 w-5 text-neutral-600 dark:text-neutral-400" />
          <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-50">
            {t('categories.title', 'Categories')}
          </h3>
        </div>
        <Button size="sm" onClick={handleCreateRoot}>
          <Plus className="mr-2 h-4 w-4" />
          {t('categories.createRoot', 'New Root')}
        </Button>
      </div>

      {/* Tree */}
      <Card className="p-4">
        {tree.length === 0 ? (
          <div className="text-center py-8">
            <div className="mx-auto w-12 h-12 rounded-full bg-neutral-100 dark:bg-neutral-800 flex items-center justify-center mb-4">
              <FolderTree className="h-6 w-6 text-neutral-400" />
            </div>
            <p className="text-neutral-600 dark:text-neutral-400 mb-4">
              {t('categories.noCategories', 'No categories yet')}
            </p>
            <Button size="sm" onClick={handleCreateRoot}>
              <Plus className="mr-2 h-4 w-4" />
              {t('categories.createFirst', 'Create First Category')}
            </Button>
          </div>
        ) : (
          <div className="space-y-1">
            {tree.map((category) => (
              <CategoryNode
                key={category.id}
                category={category}
                expanded={expandedIds.has(category.id)}
                selected={selectedCategoryId === category.id}
                onToggleExpand={handleToggleExpand}
                onSelect={handleCategorySelect}
                onCreateChild={handleCreateChild}
                onUpdate={handleCategoryUpdated}
                onDelete={handleCategoryDeleted}
              />
            ))}
          </div>
        )}
      </Card>

      {/* Create Dialog */}
      <CategoryDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
        projectId={projectId}
        parentId={createParentId}
        onSuccess={handleCategoryCreated}
      />
    </div>
  );
}
