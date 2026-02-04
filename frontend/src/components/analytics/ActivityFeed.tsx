/**
 * ActivityFeed Component
 * Real-time activity feed with infinite scroll
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { Loader2, FileText, Search, MessageSquare, Sparkles, FolderPlus } from 'lucide-react';
import { analyticsApi } from '@/lib/api';
import type { ActivityEvent } from '@/types/api';

interface ActivityFeedProps {
  projectId: number;
  maxHeight?: string;
}

export function ActivityFeed({ projectId, maxHeight = '400px' }: ActivityFeedProps) {
  const [activities, setActivities] = useState<ActivityEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [offset, setOffset] = useState(0);
  const [totalCount, setTotalCount] = useState(0);
  const observerRef = useRef<IntersectionObserver | null>(null);
  const loadMoreRef = useRef<HTMLDivElement>(null);

  const limit = 20;

  // Load activities from API
  const loadActivities = useCallback(async (newOffset: number, replace = false) => {
    if (loading) return;

    try {
      setLoading(true);
      const response = await analyticsApi.getActivity(projectId, limit, newOffset);
      const data = response.data;

      setActivities((prev) => replace ? data.activities : [...prev, ...data.activities]);
      setTotalCount(data.total_count);
      setOffset(newOffset + limit);
      setHasMore(newOffset + data.activities.length < data.total_count);
    } catch (error) {
      console.error('Failed to load activities:', error);
    } finally {
      setLoading(false);
    }
  }, [loading, projectId, limit]);

  // Load initial activities
  useEffect(() => {
    loadActivities(0, true);
  }, [loadActivities]);

  // Setup intersection observer for infinite scroll
  useEffect(() => {
    if (observerRef.current) observerRef.current.disconnect();

    observerRef.current = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loading) {
          loadActivities(offset);
        }
      },
      { threshold: 0.1 }
    );

    if (loadMoreRef.current) {
      observerRef.current.observe(loadMoreRef.current);
    }

    return () => {
      if (observerRef.current) observerRef.current.disconnect();
    };
  }, [hasMore, loading, offset, loadActivities]);

  // Get icon for event type
  const getEventIcon = (eventType: string) => {
    if (eventType.startsWith('document.')) return FileText;
    if (eventType.startsWith('search.')) return Search;
    if (eventType.startsWith('chat.')) return MessageSquare;
    if (eventType.startsWith('insight.')) return Sparkles;
    if (eventType.startsWith('category.')) return FolderPlus;
    return FileText;
  };

  // Get color for event type
  const getEventColor = (eventType: string) => {
    if (eventType.startsWith('document.')) return 'text-blue-600 dark:text-blue-400';
    if (eventType.startsWith('search.')) return 'text-green-600 dark:text-green-400';
    if (eventType.startsWith('chat.')) return 'text-orange-600 dark:text-orange-400';
    if (eventType.startsWith('insight.')) return 'text-purple-600 dark:text-purple-400';
    if (eventType.startsWith('category.')) return 'text-pink-600 dark:text-pink-400';
    return 'text-neutral-600 dark:text-neutral-400';
  };

  // Format event description
  const getEventDescription = (activity: ActivityEvent) => {
    const { event_type, event_data } = activity;

    switch (event_type) {
      case 'document.uploaded':
        return `Przesłano dokument: ${event_data.filename || 'Brak nazwy'}`;
      case 'document.deleted':
        return `Usunięto dokument`;
      case 'search.performed':
        return `Wyszukiwanie: "${event_data.query?.substring(0, 50) || '...'}"`;
      case 'chat.message_sent':
        return `Wysłano wiadomość w czacie`;
      case 'insight.generated':
        return `Wygenerowano insight: ${event_data.insight_type || 'ogólny'}`;
      case 'category.created':
        return `Utworzono kategorię`;
      case 'category.tree_generated':
        return `Wygenerowano drzewo kategorii`;
      default:
        return event_type.replace(/\./g, ' ').replace(/_/g, ' ');
    }
  };

  // Format time ago
  const getTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (seconds < 60) return 'przed chwilą';
    if (seconds < 3600) return `${Math.floor(seconds / 60)} min temu`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)} godz temu`;
    if (seconds < 604800) return `${Math.floor(seconds / 86400)} dni temu`;
    return date.toLocaleDateString('pl-PL', { month: 'short', day: 'numeric' });
  };

  return (
    <div
      className="space-y-3 overflow-y-auto pr-2"
      style={{ maxHeight }}
    >
      {activities.length === 0 && !loading ? (
        <div className="text-center py-8 text-neutral-500 dark:text-neutral-400">
          Brak aktywności do wyświetlenia
        </div>
      ) : (
        <>
          {activities.map((activity) => {
            const Icon = getEventIcon(activity.event_type);
            const colorClass = getEventColor(activity.event_type);

            return (
              <div
                key={activity.id}
                className="flex items-start gap-3 p-3 rounded-lg border border-neutral-200 dark:border-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-800/50 transition-colors"
              >
                <div className={`mt-0.5 ${colorClass}`}>
                  <Icon className="h-5 w-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-neutral-900 dark:text-neutral-50 font-medium truncate">
                    {getEventDescription(activity)}
                  </p>
                  <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-1">
                    {getTimeAgo(activity.created_at)}
                  </p>
                </div>
              </div>
            );
          })}

          {/* Infinite scroll trigger */}
          <div ref={loadMoreRef} className="py-4 text-center">
            {loading && (
              <div className="flex items-center justify-center gap-2">
                <Loader2 className="h-5 w-5 animate-spin text-neutral-400" />
                <span className="text-sm text-neutral-500 dark:text-neutral-400">
                  Ładowanie...
                </span>
              </div>
            )}
            {!hasMore && activities.length > 0 && (
              <p className="text-sm text-neutral-500 dark:text-neutral-400">
                Koniec aktywności ({totalCount} wszystkich)
              </p>
            )}
          </div>
        </>
      )}
    </div>
  );
}
