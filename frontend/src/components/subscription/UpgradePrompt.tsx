/**
 * UpgradePrompt Component
 * Displays prominent upgrade banner when usage limits are reached
 */

import { Alert, AlertDescription, AlertTitle } from '../ui/alert';
import { Button } from '../ui/button';
import { TrendingUp, XCircle } from 'lucide-react';
import { useSubscription } from '../../context/SubscriptionContext';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useState } from 'react';

export function UpgradePrompt() {
  const { t } = useTranslation();
  const { isLimitReached, isDemoMode, subscription } = useSubscription();
  const navigate = useNavigate();
  const [dismissed, setDismissed] = useState(false);

  // Don't show in demo mode or if user is already on enterprise
  if (isDemoMode || subscription?.plan === 'enterprise' || dismissed) {
    return null;
  }

  // Check which limits are reached
  const messagesLimit = isLimitReached('messages');
  const documentsLimit = isLimitReached('documents');
  const storageLimit = isLimitReached('storage');

  const anyLimitReached = messagesLimit || documentsLimit || storageLimit;

  if (!anyLimitReached) return null;

  const getLimitMessages = (): string[] => {
    const messages: string[] = [];
    if (messagesLimit) messages.push(t('upgrade.messagesLimit', 'Wiadomości'));
    if (documentsLimit) messages.push(t('upgrade.documentsLimit', 'Dokumenty'));
    if (storageLimit) messages.push(t('upgrade.storageLimit', 'Pamięć'));
    return messages;
  };

  const limitMessages = getLimitMessages();

  return (
    <Alert className="mb-6 border-orange-500 bg-orange-50 dark:bg-orange-950">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <AlertTitle className="flex items-center gap-2 text-orange-700 dark:text-orange-300">
            <TrendingUp className="w-5 h-5" />
            {t('upgrade.title', 'Osiągnięto Limit')}
          </AlertTitle>
          <AlertDescription className="text-orange-600 dark:text-orange-400 mt-2">
            {t('upgrade.description', 'Osiągnąłeś limit dla:')} {limitMessages.join(', ')}
            <br />
            {t('upgrade.action', 'Ulepsz swój plan, aby kontynuować korzystanie z pełnych możliwości.')}
          </AlertDescription>
          <div className="flex gap-2 mt-4">
            <Button
              onClick={() => navigate('/account')}
              className="flex items-center gap-2"
              size="sm"
            >
              <TrendingUp className="w-4 h-4" />
              {t('upgrade.button', 'Ulepsz Plan')}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate('/pricing')}
            >
              {t('upgrade.viewPlans', 'Zobacz Plany')}
            </Button>
          </div>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setDismissed(true)}
          className="text-orange-700 dark:text-orange-300 hover:text-orange-900 dark:hover:text-orange-100"
        >
          <XCircle className="w-4 h-4" />
        </Button>
      </div>
    </Alert>
  );
}
