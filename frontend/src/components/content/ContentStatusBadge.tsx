/**
 * ContentStatusBadge - Content Status Badge Component
 *
 * Displays content status with appropriate styling
 */

import { useTranslation } from 'react-i18next';
import { Badge } from '@/components/ui/badge';
import type { ContentStatus } from '@/types/content';

interface ContentStatusBadgeProps {
  status: ContentStatus;
  publishedAt?: string | null;
  className?: string;
}

export function ContentStatusBadge({
  status,
  publishedAt,
  className
}: ContentStatusBadgeProps) {
  const { t } = useTranslation();

  const getVariant = (status: ContentStatus) => {
    switch (status) {
      case 'published':
        return 'default';
      case 'review':
        return 'secondary';
      case 'draft':
      default:
        return 'outline';
    }
  };

  return (
    <div className={className}>
      <Badge variant={getVariant(status)}>
        {t(`contentWorkbench.status.${status}`)}
      </Badge>
      {status === 'published' && publishedAt && (
        <span className="text-xs text-muted-foreground ml-2">
          {new Date(publishedAt).toLocaleDateString('pl-PL')}
        </span>
      )}
    </div>
  );
}
