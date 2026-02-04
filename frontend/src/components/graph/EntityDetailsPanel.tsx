/**
 * Entity Details Panel Component
 * Display detailed information about selected entity and its neighbors
 * Phase 3: Knowledge Graph Visualization
 */

import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import graphApi from '@/lib/api/graphApi';
import type { GraphNode, EntityDetailsResponse } from '@/types/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  Loader2,
  X,
  Network,
  TrendingUp,
  Link2,
  Activity,
} from 'lucide-react';

interface EntityDetailsPanelProps {
  entity: GraphNode | null;
  onClose?: () => void;
  projectId?: number;
}

export function EntityDetailsPanel({
  entity,
  onClose,
}: EntityDetailsPanelProps) {
  const { t } = useTranslation();
  const [details, setDetails] = useState<EntityDetailsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Load entity details when entity changes
  useEffect(() => {
    if (entity) {
      loadEntityDetails();
    } else {
      setDetails(null);
    }
  }, [entity]);

  const loadEntityDetails = async () => {
    if (!entity) return;

    try {
      setLoading(true);
      setError('');

      const response = await graphApi.getEntityDetails(entity.id, {
        depth: 2,
        min_weight: 0.0,
      });

      setDetails(response.data);
    } catch (err) {
      console.error('Failed to load entity details:', err);
      setError(t('errors.loadEntityDetailsFailed'));
    } finally {
      setLoading(false);
    }
  };

  if (!entity) {
    return (
      <Card className="h-[calc(100vh-12rem)] flex items-center justify-center">
        <CardContent className="text-center py-12">
          <Network className="h-16 w-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {t('graph.selectEntity')}
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-[calc(100vh-12rem)] flex flex-col">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <CardTitle className="text-lg truncate">{entity.name}</CardTitle>
            <CardDescription className="mt-1">
              <Badge variant="secondary" className="text-xs">
                {entity.type}
              </Badge>
            </CardDescription>
          </div>
          {onClose && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="shrink-0"
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
      </CardHeader>

      <CardContent className="flex-1 overflow-hidden p-0">
        <ScrollArea className="h-full px-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
              <Button
                variant="outline"
                size="sm"
                onClick={loadEntityDetails}
                className="mt-4"
              >
                {t('common.retry')}
              </Button>
            </div>
          ) : details ? (
            <div className="space-y-6 pb-6">
              {/* Basic Info */}
              <div>
                <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                  <Activity className="h-4 w-4" />
                  {t('graph.basicInfo')}
                </h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">
                      {t('graph.occurrences')}:
                    </span>
                    <span className="font-medium">
                      {details.occurrence_count}
                    </span>
                  </div>
                  {details.community !== undefined && (
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">
                        {t('graph.community')}:
                      </span>
                      <Badge variant="outline" className="text-xs">
                        #{details.community}
                      </Badge>
                    </div>
                  )}
                  {details.clustering !== undefined && (
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">
                        {t('graph.clustering')}:
                      </span>
                      <span className="font-medium">
                        {(details.clustering * 100).toFixed(1)}%
                      </span>
                    </div>
                  )}
                </div>
              </div>

              <Separator />

              {/* Centrality Metrics */}
              {details.centrality && (
                <>
                  <div>
                    <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                      <TrendingUp className="h-4 w-4" />
                      {t('graph.centralityMetrics')}
                    </h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between items-center">
                        <span className="text-gray-600 dark:text-gray-400">
                          {t('graph.degree')}:
                        </span>
                        <div className="flex items-center gap-2">
                          <div className="w-24 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-blue-600 dark:bg-blue-500 transition-all"
                              style={{ width: `${details.centrality.degree * 100}%` }}
                            />
                          </div>
                          <span className="font-medium text-xs w-12 text-right">
                            {(details.centrality.degree * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-gray-600 dark:text-gray-400">
                          {t('graph.betweenness')}:
                        </span>
                        <div className="flex items-center gap-2">
                          <div className="w-24 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-green-600 dark:bg-green-500 transition-all"
                              style={{ width: `${details.centrality.betweenness * 100}%` }}
                            />
                          </div>
                          <span className="font-medium text-xs w-12 text-right">
                            {(details.centrality.betweenness * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-gray-600 dark:text-gray-400">
                          {t('graph.closeness')}:
                        </span>
                        <div className="flex items-center gap-2">
                          <div className="w-24 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-purple-600 dark:bg-purple-500 transition-all"
                              style={{ width: `${details.centrality.closeness * 100}%` }}
                            />
                          </div>
                          <span className="font-medium text-xs w-12 text-right">
                            {(details.centrality.closeness * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-gray-600 dark:text-gray-400">
                          {t('graph.eigenvector')}:
                        </span>
                        <div className="flex items-center gap-2">
                          <div className="w-24 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-orange-600 dark:bg-orange-500 transition-all"
                              style={{ width: `${details.centrality.eigenvector * 100}%` }}
                            />
                          </div>
                          <span className="font-medium text-xs w-12 text-right">
                            {(details.centrality.eigenvector * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <Separator />
                </>
              )}

              {/* Neighbors */}
              {details.neighbors && details.neighbors.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                    <Link2 className="h-4 w-4" />
                    {t('graph.neighbors')} ({details.neighbors.length})
                  </h3>
                  <div className="space-y-2">
                    {details.neighbors.slice(0, 10).map((neighbor) => (
                      <div
                        key={neighbor.id}
                        className="flex items-center justify-between p-2 rounded-lg bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                      >
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                            {neighbor.name}
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            {t('graph.distance')}: {neighbor.distance} {t('graph.hops')}
                          </p>
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400 ml-2">
                          {(neighbor.path_weight * 100).toFixed(0)}%
                        </div>
                      </div>
                    ))}
                    {details.neighbors.length > 10 && (
                      <p className="text-xs text-gray-500 dark:text-gray-400 text-center pt-2">
                        +{details.neighbors.length - 10} {t('graph.moreNeighbors')}
                      </p>
                    )}
                  </div>
                </div>
              )}
            </div>
          ) : null}
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
