/**
 * CategoryTree Component - Hierarchical Category Tree Visualization
 *
 * Features:
 * - Recursive tree rendering with expand/collapse
 * - Color-coded categories
 * - Icon display
 * - Selection state
 * - Depth-based indentation
 */

import { useState } from 'react';
import { ChevronRight, ChevronDown } from 'lucide-react';
import * as Icons from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Category } from '@/types/api';

interface CategoryTreeProps {
  categories: Category[];
  selectedCategory: Category | null;
  onCategorySelect: (category: Category) => void;
  className?: string;
}

interface CategoryNodeProps {
  category: Category;
  children: Category[];
  selectedCategory: Category | null;
  onCategorySelect: (category: Category) => void;
  depth?: number;
}

function CategoryNode({
  category,
  children,
  selectedCategory,
  onCategorySelect,
  depth = 0
}: CategoryNodeProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const hasChildren = children.length > 0;
  const isSelected = selectedCategory?.id === category.id;

  // Get Lucide icon component dynamically
  const IconComponent = (Icons as any)[category.icon || 'Folder'] || Icons.Folder;

  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (hasChildren) {
      setIsExpanded(!isExpanded);
    }
  };

  const handleSelect = () => {
    onCategorySelect(category);
  };

  return (
    <div>
      {/* Category row */}
      <div
        className={cn(
          'flex items-center gap-2 px-2 py-1.5 rounded-md cursor-pointer hover:bg-accent transition-colors',
          isSelected && 'bg-accent font-medium'
        )}
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
        onClick={handleSelect}
      >
        {/* Expand/collapse button */}
        <button
          onClick={handleToggle}
          className="flex-shrink-0 w-4 h-4 flex items-center justify-center hover:bg-accent-foreground/10 rounded"
        >
          {hasChildren ? (
            isExpanded ? (
              <ChevronDown className="h-3 w-3" />
            ) : (
              <ChevronRight className="h-3 w-3" />
            )
          ) : (
            <span className="w-3" />
          )}
        </button>

        {/* Category icon with color */}
        <div
          className="flex-shrink-0 w-6 h-6 rounded flex items-center justify-center"
          style={{ backgroundColor: category.color }}
        >
          <IconComponent className="h-4 w-4 text-gray-700" />
        </div>

        {/* Category name */}
        <span className="flex-1 text-sm truncate">{category.name}</span>

        {/* Page badge */}
        {category.page_start && (
          <span className="flex-shrink-0 text-xs text-muted-foreground">
            p.{category.page_start}
          </span>
        )}
      </div>

      {/* Children */}
      {hasChildren && isExpanded && (
        <div>
          {children.map(child => (
            <CategoryTreeNode
              key={child.id}
              category={child}
              categories={children}
              selectedCategory={selectedCategory}
              onCategorySelect={onCategorySelect}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function CategoryTreeNode({
  category,
  categories,
  selectedCategory,
  onCategorySelect,
  depth
}: {
  category: Category;
  categories: Category[];
  selectedCategory: Category | null;
  onCategorySelect: (category: Category) => void;
  depth: number;
}) {
  // Find children of this category
  const children = categories.filter(c => c.parent_id === category.id);

  return (
    <CategoryNode
      category={category}
      children={children}
      selectedCategory={selectedCategory}
      onCategorySelect={onCategorySelect}
      depth={depth}
    />
  );
}

export function CategoryTree({
  categories,
  selectedCategory,
  onCategorySelect,
  className
}: CategoryTreeProps) {
  if (categories.length === 0) {
    return (
      <div className={cn('text-center text-sm text-muted-foreground py-8', className)}>
        Brak kategorii
      </div>
    );
  }

  // Find root categories (parent_id is null or 0)
  const rootCategories = categories.filter(
    c => c.parent_id === null || c.parent_id === 0 || c.parent_id === undefined
  );

  if (rootCategories.length === 0) {
    return (
      <div className={cn('text-center text-sm text-muted-foreground py-8', className)}>
        Brak kategorii głównych
      </div>
    );
  }

  return (
    <div className={cn('space-y-1', className)}>
      {rootCategories.map(rootCategory => (
        <CategoryTreeNode
          key={rootCategory.id}
          category={rootCategory}
          categories={categories}
          selectedCategory={selectedCategory}
          onCategorySelect={onCategorySelect}
          depth={0}
        />
      ))}
    </div>
  );
}
