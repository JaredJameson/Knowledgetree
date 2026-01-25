/**
 * CategoryDialog Component
 * Create and edit category dialog with color picker
 */

import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { categoriesApi } from '@/lib/api';
import type { Category } from '@/types/api';
import { Button } from '@/components/ui/button';
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
} from '@/components/ui/dialog';
import { Loader2 } from 'lucide-react';

interface CategoryDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projectId: number;
  parentId?: number | null;
  category?: Category;
  onSuccess: () => void;
}

// Predefined colors
const PRESET_COLORS = [
  '#E6E6FA', // Lavender
  '#FFE4E1', // Misty Rose
  '#E0FFE0', // Light Green
  '#FFE4B5', // Moccasin
  '#E0F2F7', // Light Cyan
  '#FFF0E6', // Floral White
  '#F0E6FF', // Light Purple
  '#FFE6F0', // Light Pink
];

export function CategoryDialog({
  open,
  onOpenChange,
  projectId,
  parentId,
  category,
  onSuccess,
}: CategoryDialogProps) {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [color, setColor] = useState('#E6E6FA');
  const [customColor, setCustomColor] = useState('');

  const isEdit = !!category;

  // Initialize form when dialog opens or category changes
  useEffect(() => {
    if (open) {
      if (category) {
        setName(category.name);
        setDescription(category.description || '');
        setColor(category.color);
        setCustomColor(category.color);
      } else {
        setName('');
        setDescription('');
        setColor('#E6E6FA');
        setCustomColor('');
      }
    }
  }, [open, category]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!name.trim()) return;

    try {
      setLoading(true);

      const data = {
        name: name.trim(),
        description: description.trim() || undefined,
        color: customColor || color,
        parent_id: parentId,
      };

      if (isEdit && category) {
        await categoriesApi.update(category.id, data);
      } else {
        await categoriesApi.create(projectId, data);
      }

      onSuccess();
    } catch (err) {
      console.error('Failed to save category:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleColorSelect = (selectedColor: string) => {
    setColor(selectedColor);
    setCustomColor('');
  };

  const handleCustomColorChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newColor = e.target.value;
    setCustomColor(newColor);
    setColor(newColor);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>
              {isEdit
                ? t('categories.edit.title', 'Edit Category')
                : parentId
                ? t('categories.create.titleChild', 'Create Subcategory')
                : t('categories.create.title', 'Create Category')}
            </DialogTitle>
            <DialogDescription>
              {isEdit
                ? t('categories.edit.description', 'Update category details')
                : t('categories.create.description', 'Add a new category to organize your documents')}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            {/* Name */}
            <div className="space-y-2">
              <Label htmlFor="category-name">
                {t('categories.form.name', 'Name')} *
              </Label>
              <Input
                id="category-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder={t('categories.form.namePlaceholder', 'e.g., Research Papers')}
                disabled={loading}
                required
              />
            </div>

            {/* Description */}
            <div className="space-y-2">
              <Label htmlFor="category-description">
                {t('categories.form.description', 'Description')}
              </Label>
              <Textarea
                id="category-description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder={t('categories.form.descriptionPlaceholder', 'Optional description')}
                disabled={loading}
                rows={2}
              />
            </div>

            {/* Color Picker */}
            <div className="space-y-2">
              <Label>{t('categories.form.color', 'Color')}</Label>
              <div className="grid grid-cols-8 gap-2">
                {PRESET_COLORS.map((presetColor) => (
                  <button
                    key={presetColor}
                    type="button"
                    onClick={() => handleColorSelect(presetColor)}
                    className={`w-8 h-8 rounded-md border-2 transition-all ${
                      color === presetColor && !customColor
                        ? 'border-primary-600 scale-110'
                        : 'border-neutral-300 dark:border-neutral-600 hover:scale-105'
                    }`}
                    style={{ backgroundColor: presetColor }}
                    disabled={loading}
                    title={presetColor}
                  />
                ))}
              </div>

              {/* Custom Color Input */}
              <div className="flex items-center gap-2 mt-2">
                <Label htmlFor="custom-color" className="text-sm">
                  {t('categories.form.customColor', 'Custom:')}
                </Label>
                <Input
                  id="custom-color"
                  type="color"
                  value={customColor || color}
                  onChange={handleCustomColorChange}
                  className="w-20 h-8 p-1 cursor-pointer"
                  disabled={loading}
                />
                <span className="text-sm text-neutral-600 dark:text-neutral-400">
                  {customColor || color}
                </span>
              </div>
            </div>

            {/* Preview */}
            <div className="space-y-2">
              <Label>{t('categories.form.preview', 'Preview')}</Label>
              <div
                className="flex items-center gap-2 px-3 py-2 rounded-md border border-neutral-300 dark:border-neutral-600"
                style={{ backgroundColor: `${customColor || color}20` }}
              >
                <div
                  className="w-4 h-4 rounded"
                  style={{ backgroundColor: customColor || color }}
                />
                <span className="text-sm font-medium text-neutral-900 dark:text-neutral-50">
                  {name || t('categories.form.namePlaceholder', 'Category Name')}
                </span>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={loading}
            >
              {t('common.cancel', 'Cancel')}
            </Button>
            <Button type="submit" disabled={loading || !name.trim()}>
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {loading
                ? isEdit
                  ? t('categories.edit.updating', 'Updating...')
                  : t('categories.create.creating', 'Creating...')
                : isEdit
                ? t('categories.edit.submit', 'Update')
                : t('categories.create.submit', 'Create')}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
