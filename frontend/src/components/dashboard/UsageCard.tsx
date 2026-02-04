/**
 * UsageCard Component
 * Displays current usage with progress bars and upgrade prompts
 */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Progress } from '../ui/progress';
import { Button } from '../ui/button';
import { TrendingUp, AlertTriangle } from 'lucide-react';
import { useSubscription } from '../../context/SubscriptionContext';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

export function UsageCard() {
  const { t } = useTranslation();
  const { usage, getUsagePercentage, isLimitReached, isDemoMode, loading } = useSubscription();
  const navigate = useNavigate();

  if (loading || !usage) return null;

  const messagesPercent = getUsagePercentage('messages');
  const documentsPercent = getUsagePercentage('documents');
  const storagePercent = getUsagePercentage('storage');

  // Check if any metric is above 80%
  const nearLimit = messagesPercent > 80 || documentsPercent > 80 || storagePercent > 80;

  const formatValue = (used: number, limit: number | null, metric: string): string => {
    if (limit === null) return `${used} / ∞`;

    if (metric === 'storage') {
      const usedGB = (used / 1024).toFixed(1);
      return `${usedGB} GB / ${limit} GB`;
    }

    return `${used} / ${limit}`;
  };

  return (
    <Card className={nearLimit ? 'border-orange-500' : ''}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              {t('dashboard.usage.title', 'Użycie')}
              {nearLimit && !isDemoMode && (
                <AlertTriangle className="w-4 h-4 text-orange-600" />
              )}
            </CardTitle>
            <CardDescription>
              {isDemoMode
                ? t('dashboard.usage.demoDescription', 'Nieograniczone użycie w trybie demo')
                : t('dashboard.usage.description', 'Twoje użycie w bieżącym okresie')}
            </CardDescription>
          </div>
          {nearLimit && !isDemoMode && (
            <Button
              size="sm"
              onClick={() => navigate('/account')}
              className="flex items-center gap-2"
            >
              <TrendingUp className="w-4 h-4" />
              {t('dashboard.usage.upgrade', 'Ulepsz')}
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Messages */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium">
                {t('dashboard.usage.messages', 'Wiadomości')}
              </span>
              <span className="text-sm text-muted-foreground">
                {formatValue(usage.messages.used, usage.messages.limit, 'messages')}
              </span>
            </div>
            <Progress value={messagesPercent} className="h-2" />
            {isLimitReached('messages') && (
              <p className="text-xs text-red-600 mt-1">
                {t('dashboard.usage.limitReached', 'Limit osiągnięty')}
              </p>
            )}
          </div>

          {/* Documents */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium">
                {t('dashboard.usage.documents', 'Dokumenty')}
              </span>
              <span className="text-sm text-muted-foreground">
                {formatValue(usage.documents.used, usage.documents.limit, 'documents')}
              </span>
            </div>
            <Progress value={documentsPercent} className="h-2" />
            {isLimitReached('documents') && (
              <p className="text-xs text-red-600 mt-1">
                {t('dashboard.usage.limitReached', 'Limit osiągnięty')}
              </p>
            )}
          </div>

          {/* Storage */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium">
                {t('dashboard.usage.storage', 'Pamięć')}
              </span>
              <span className="text-sm text-muted-foreground">
                {formatValue(usage.storage.used, usage.storage.limit, 'storage')}
              </span>
            </div>
            <Progress value={storagePercent} className="h-2" />
            {isLimitReached('storage') && (
              <p className="text-xs text-red-600 mt-1">
                {t('dashboard.usage.limitReached', 'Limit osiągnięty')}
              </p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
