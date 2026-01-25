/**
 * CategoryTreeArtifact Component
 * Displays interactive category tree in ArtifactPanel
 */

import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { categoriesApi } from '@/lib/api';
import type { CategoryTreeNode } from '@/types/api';
import { CategoryTree } from '@/components/categories/CategoryTree';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Loader2, FolderTree, RefreshCw, ExternalLink } from 'lucide-react';

interface CategoryTreeArtifactProps {
  projectId: number;
  categoryIds?: number[];
  sourceUrl?: string;
  sourceType?: string;
  metadata?: Record<string, any>;
  onRefresh?: () => void;
}

export function CategoryTreeArtifact({
  projectId,
  categoryIds,
  sourceUrl,
  sourceType = 'unknown',
  metadata,
  onRefresh,
}: CategoryTreeArtifactProps) {
  const { t } = useTranslation();
  const [tree, setTree] = useState<CategoryTreeNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedCategoryId, setSelectedCategoryId] = useState<number | null>(null);

  // Load category tree
  useEffect(() => {
    loadTree();
  }, [projectId]);

  // Auto-refresh if we have specific category IDs and they might not be loaded yet
  useEffect(() => {
    if (categoryIds && categoryIds.length > 0 && tree.length === 0 && !loading) {
      const timer = setTimeout(loadTree, 500);
      return () => clearTimeout(timer);
    }
  }, [categoryIds, tree, loading]);

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

  const handleCategorySelect = (category: CategoryTreeNode | null) => {
    setSelectedCategoryId(category?.id || null);
  };

  const handleRefresh = () => {
    loadTree();
    onRefresh?.();
  };

  const categoryCount = metadata?.categories_created || 0;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-primary-100 dark:bg-primary-900/30">
            <FolderTree className="h-5 w-5 text-primary-600 dark:text-primary-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-50">
              {t('artifacts.categoryTree.title', 'Knowledge Tree')}
            </h3>
            <p className="text-sm text-neutral-600 dark:text-neutral-400">
              {t('artifacts.categoryTree.description', 'Interactive hierarchical tree - edit, expand, organize')}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="secondary" className="text-sm">
            {categoryCount} {categoryCount === 1 ? 'category' : 'categories'}
          </Badge>
          <Button size="sm" variant="ghost" onClick={handleRefresh} disabled={loading}>
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </div>

      {/* Source Info */}
      {(sourceUrl || sourceType) && (
        <Card className="p-3 bg-neutral-50 dark:bg-neutral-900">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2 text-neutral-600 dark:text-neutral-400">
              <span className="font-medium">Source:</span>
              <Badge variant="outline" className="text-xs">
                {sourceType}
              </Badge>
            </div>
            {sourceUrl && (
              <a
                href={sourceUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 text-primary-600 hover:text-primary-700 text-xs"
              >
                <ExternalLink className="h-3 w-3" />
                Open
              </a>
            )}
          </div>
        </Card>
      )}

      {/* Category Tree */}
      <Card className="p-4">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-primary-600" />
            <span className="ml-2 text-sm text-neutral-600 dark:text-neutral-400">
              {t('artifacts.categoryTree.loading', 'Loading tree...')}
            </span>
          </div>
        ) : error ? (
          <div className="text-center py-8">
            <p className="text-error-600 dark:text-error-400">{error}</p>
            <Button size="sm" variant="outline" onClick={handleRefresh} className="mt-4">
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </div>
        ) : tree.length === 0 ? (
          <div className="text-center py-8">
            <FolderTree className="mx-auto h-12 w-12 text-neutral-400 mb-4" />
            <p className="text-neutral-600 dark:text-neutral-400 mb-1">
              {t('artifacts.categoryTree.empty', 'No categories yet')}
            </p>
            <p className="text-sm text-neutral-500 dark:text-neutral-500">
              {t('artifacts.categoryTree.emptyHint', 'The tree will appear here as content is processed')}
            </p>
          </div>
        ) : (
          <CategoryTree
            projectId={projectId}
            onCategorySelect={handleCategorySelect}
            selectedCategoryId={selectedCategoryId}
          />
        )}
      </Card>

      {/* Selected Category Info */}
      {selectedCategoryId && (
        <Card className="p-3 bg-primary-50 dark:bg-primary-900/20 border-primary-200 dark:border-primary-800">
          <p className="text-sm text-primary-700 dark:text-primary-300">
            ✓ Selected category ID: {selectedCategoryId}
          </p>
          <p className="text-xs text-primary-600 dark:text-primary-400 mt-1">
            Click on categories to navigate. Use hover actions to edit, add children, or delete.
          </p>
        </Card>
      )}

      {/* Instructions */}
      <Card className="p-3 bg-neutral-50 dark:bg-neutral-900">
        <h4 className="text-sm font-medium mb-2">💡 Tips:</h4>
        <ul className="text-xs text-neutral-600 dark:text-neutral-400 space-y-1">
          <li>• Click <strong>►</strong> to expand/collapse categories</li>
          <li>• Hover over category to see <strong>Edit</strong>, <strong>Add</strong>, <strong>Delete</strong> buttons</li>
          <li>• Create hierarchical structure by adding subcategories</li>
          <li>• All changes are saved automatically to the database</li>
        </ul>
      </Card>
    </div>
  );
}
