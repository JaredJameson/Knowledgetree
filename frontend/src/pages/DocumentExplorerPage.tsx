/**
 * Document Explorer Page - Interactive Category Tree Navigation
 *
 * Features:
 * - Hierarchical category tree visualization
 * - Category content viewing (chunks, tables, formulas)
 * - Document structure navigation
 * - Content assignment and management
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, FileText, Table as TableIcon, Calculator, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { CategoryTree } from '@/components/CategoryTree';
import { documentsApi, categoriesApi } from '@/lib/api';
import type { Category, Document } from '@/types/api';

export function DocumentExplorerPage() {
  const { documentId } = useParams<{ documentId: string }>();
  const navigate = useNavigate();
  const { t } = useTranslation();

  const [document, setDocument] = useState<Document | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<Category | null>(null);
  const [categoryContent, setCategoryContent] = useState<any>(null);
  const [loadingContent, setLoadingContent] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (documentId) {
      loadDocumentAndCategories(parseInt(documentId));
    }
  }, [documentId]);

  const loadDocumentAndCategories = async (docId: number) => {
    try {
      setLoading(true);

      // Load document
      const docResponse = await documentsApi.get(docId);
      setDocument(docResponse.data);

      // Load categories for the project
      if (docResponse.data.project_id) {
        const categoriesResponse = await categoriesApi.list(docResponse.data.project_id, undefined, 1, 1000);
        setCategories(categoriesResponse.data.categories || []);
      }
    } catch (error) {
      console.error('Failed to load document explorer:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCategorySelect = async (category: Category) => {
    setSelectedCategory(category);

    // Load content for this category
    try {
      setLoadingContent(true);
      const response = await categoriesApi.getContent(category.id);
      setCategoryContent(response.data);
    } catch (error) {
      console.error('Failed to load category content:', error);
      setCategoryContent(null);
    } finally {
      setLoadingContent(false);
    }
  };

  const handleBack = () => {
    navigate(-1);
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <div className="flex items-center gap-2">
            <Loader2 className="h-6 w-6 animate-spin" />
            <span>{t('documentExplorer.loading', 'Ładowanie...')}</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={handleBack}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold">
              {t('documentExplorer.title', 'Document Explorer')}
            </h1>
            <p className="text-sm text-muted-foreground">
              {document?.filename || t('documentExplorer.loading', 'Loading document...')}
            </p>
          </div>
        </div>
      </div>

      {/* Two-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column: Category Tree */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>{t('documentExplorer.categoryTree', 'Category Tree')}</CardTitle>
            <CardDescription>
              {t('documentExplorer.categoryTreeDescription', 'Navigate document structure')}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <CategoryTree
              categories={categories}
              selectedCategory={selectedCategory}
              onCategorySelect={handleCategorySelect}
            />
          </CardContent>
        </Card>

        {/* Right column: Category Content */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>
              {selectedCategory
                ? selectedCategory.name
                : t('documentExplorer.selectCategory', 'Select a category')}
            </CardTitle>
            <CardDescription>
              {selectedCategory
                ? t('documentExplorer.categoryContent', 'Category content and details')
                : t('documentExplorer.selectCategoryDescription', 'Choose a category to view its content')}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {selectedCategory ? (
              <div className="space-y-6">
                {/* Category metadata */}
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium">{t('documentExplorer.depth', 'Depth')}:</span>{' '}
                    {selectedCategory.depth}
                  </div>
                  {selectedCategory.page_start && (
                    <div>
                      <span className="font-medium">{t('documentExplorer.pages', 'Pages')}:</span>{' '}
                      {selectedCategory.page_start}
                      {selectedCategory.page_end && ` - ${selectedCategory.page_end}`}
                    </div>
                  )}
                </div>

                {/* Loading state */}
                {loadingContent ? (
                  <div className="flex items-center justify-center py-12">
                    <div className="flex items-center gap-2">
                      <Loader2 className="h-5 w-5 animate-spin" />
                      <span>{t('documentExplorer.loadingContent', 'Ładowanie zawartości...')}</span>
                    </div>
                  </div>
                ) : categoryContent ? (
                  <div className="space-y-4">
                    {/* Chunks */}
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <FileText className="h-4 w-4" />
                        <h3 className="font-medium">
                          {t('documentExplorer.chunks', 'Text Chunks')} ({categoryContent.total_chunks})
                        </h3>
                      </div>
                      {categoryContent.chunks && categoryContent.chunks.length > 0 ? (
                        <div className="space-y-3">
                          {categoryContent.chunks.map((chunk: any) => (
                            <div key={chunk.id} className="p-3 bg-muted rounded-md text-sm">
                              <div className="text-xs text-muted-foreground mb-1">
                                Chunk #{chunk.chunk_index}
                              </div>
                              <div className="whitespace-pre-wrap">{chunk.text}</div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-sm text-muted-foreground">
                          {t('documentExplorer.noChunks', 'No chunks assigned to this category yet')}
                        </div>
                      )}
                    </div>

                    {/* Tables */}
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <TableIcon className="h-4 w-4" />
                        <h3 className="font-medium">
                          {t('documentExplorer.tables', 'Tables')} ({categoryContent.total_tables})
                        </h3>
                      </div>
                      {categoryContent.tables && categoryContent.tables.length > 0 ? (
                        <div className="space-y-3">
                          {categoryContent.tables.map((table: any) => (
                            <div key={table.id} className="p-3 bg-muted rounded-md text-sm">
                              <div className="text-xs text-muted-foreground mb-2">
                                Table #{table.table_index} (Page {table.page_number}) - {table.row_count}x{table.col_count}
                              </div>
                              <div className="overflow-x-auto">
                                {table.table_data && (
                                  <pre className="text-xs">{JSON.stringify(table.table_data, null, 2)}</pre>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-sm text-muted-foreground">
                          {t('documentExplorer.noTables', 'No tables assigned to this category yet')}
                        </div>
                      )}
                    </div>

                    {/* Formulas */}
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <Calculator className="h-4 w-4" />
                        <h3 className="font-medium">
                          {t('documentExplorer.formulas', 'Formulas')} ({categoryContent.total_formulas})
                        </h3>
                      </div>
                      {categoryContent.formulas && categoryContent.formulas.length > 0 ? (
                        <div className="space-y-3">
                          {categoryContent.formulas.map((formula: any) => (
                            <div key={formula.id} className="p-3 bg-muted rounded-md text-sm">
                              <div className="text-xs text-muted-foreground mb-2">
                                Formula #{formula.formula_index} (Page {formula.page_number})
                              </div>
                              <div className="font-mono text-xs mb-2">
                                {formula.latex_content}
                              </div>
                              {formula.context_before && (
                                <div className="text-xs text-muted-foreground">
                                  Before: {formula.context_before}
                                </div>
                              )}
                              {formula.context_after && (
                                <div className="text-xs text-muted-foreground">
                                  After: {formula.context_after}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-sm text-muted-foreground">
                          {t('documentExplorer.noFormulas', 'No formulas assigned to this category yet')}
                        </div>
                      )}
                    </div>
                  </div>
                ) : null}
              </div>
            ) : (
              <div className="text-center text-muted-foreground py-12">
                {t('documentExplorer.selectCategoryPrompt', 'Select a category from the tree to view its content')}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
