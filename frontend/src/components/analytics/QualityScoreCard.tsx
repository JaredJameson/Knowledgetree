/**
 * QualityScoreCard Component
 * Displays project quality score with component breakdown
 */

import { useEffect, useState, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Loader2 } from 'lucide-react';
import { analyticsApi } from '@/lib/api';
import type { QualityScoreResponse } from '@/types/api';

interface QualityScoreCardProps {
  projectId: number;
  days?: number;
}

export function QualityScoreCard({ projectId, days = 7 }: QualityScoreCardProps) {
  const [score, setScore] = useState<QualityScoreResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadQualityScore = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const response = await analyticsApi.getQualityScore(projectId, days);
      setScore(response.data);
    } catch (err) {
      console.error('Failed to load quality score:', err);
      setError('Nie udało się załadować wskaźnika jakości');
    } finally {
      setLoading(false);
    }
  }, [projectId, days]);

  useEffect(() => {
    loadQualityScore();
  }, [loadQualityScore]);

  // Get score color
  const getScoreColor = (value: number) => {
    if (value >= 70) return 'text-green-600 dark:text-green-400';
    if (value >= 40) return 'text-orange-600 dark:text-orange-400';
    return 'text-red-600 dark:text-red-400';
  };

  // Get score background
  const getScoreBg = (value: number) => {
    if (value >= 70) return 'bg-green-100 dark:bg-green-900/20';
    if (value >= 40) return 'bg-orange-100 dark:bg-orange-900/20';
    return 'bg-red-100 dark:bg-red-900/20';
  };

  // Get score label
  const getScoreLabel = (value: number) => {
    if (value >= 70) return 'Wysoka aktywność';
    if (value >= 40) return 'Umiarkowana aktywność';
    return 'Niska aktywność';
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Wskaźnik Jakości</CardTitle>
          <CardDescription>Ocena aktywności projektu</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-neutral-400" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error || !score) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Wskaźnik Jakości</CardTitle>
          <CardDescription>Ocena aktywności projektu</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-error-600 dark:text-error-400">{error || 'Brak danych'}</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Wskaźnik Jakości</CardTitle>
        <CardDescription>Ocena aktywności projektu (ostatnie {score.period_days} dni)</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Overall Score */}
        <div className="text-center">
          <div className={`inline-flex items-center justify-center w-32 h-32 rounded-full ${getScoreBg(score.overall_score)}`}>
            <div className="text-center">
              <div className={`text-4xl font-bold ${getScoreColor(score.overall_score)}`}>
                {score.overall_score}
              </div>
              <div className="text-xs text-neutral-600 dark:text-neutral-400 mt-1">
                / 100
              </div>
            </div>
          </div>
          <p className={`mt-3 font-medium ${getScoreColor(score.overall_score)}`}>
            {getScoreLabel(score.overall_score)}
          </p>
        </div>

        {/* Component Scores */}
        <div className="space-y-4">
          {/* Documents Score */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-neutral-600 dark:text-neutral-400">
                Dokumenty
              </span>
              <span className="text-sm font-medium text-neutral-900 dark:text-neutral-50">
                {score.document_score}/100
              </span>
            </div>
            <div className="w-full bg-neutral-200 dark:bg-neutral-700 rounded-full h-2">
              <div
                className="bg-blue-600 dark:bg-blue-400 h-2 rounded-full transition-all"
                style={{ width: `${score.document_score}%` }}
              />
            </div>
            <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-1">
              {score.metrics.total_documents} przesłanych w okresie
            </p>
          </div>

          {/* Search Score */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-neutral-600 dark:text-neutral-400">
                Wyszukiwania
              </span>
              <span className="text-sm font-medium text-neutral-900 dark:text-neutral-50">
                {score.search_score}/100
              </span>
            </div>
            <div className="w-full bg-neutral-200 dark:bg-neutral-700 rounded-full h-2">
              <div
                className="bg-green-600 dark:bg-green-400 h-2 rounded-full transition-all"
                style={{ width: `${score.search_score}%` }}
              />
            </div>
            <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-1">
              {score.metrics.total_searches} wyszukiwań w okresie
            </p>
          </div>

          {/* Chat Score */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-neutral-600 dark:text-neutral-400">
                Czaty
              </span>
              <span className="text-sm font-medium text-neutral-900 dark:text-neutral-50">
                {score.chat_score}/100
              </span>
            </div>
            <div className="w-full bg-neutral-200 dark:bg-neutral-700 rounded-full h-2">
              <div
                className="bg-orange-600 dark:bg-orange-400 h-2 rounded-full transition-all"
                style={{ width: `${score.chat_score}%` }}
              />
            </div>
            <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-1">
              {score.metrics.total_messages} wiadomości w okresie
            </p>
          </div>

          {/* Diversity Score */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-neutral-600 dark:text-neutral-400">
                Różnorodność treści
              </span>
              <span className="text-sm font-medium text-neutral-900 dark:text-neutral-50">
                {score.diversity_score}/100
              </span>
            </div>
            <div className="w-full bg-neutral-200 dark:bg-neutral-700 rounded-full h-2">
              <div
                className="bg-purple-600 dark:bg-purple-400 h-2 rounded-full transition-all"
                style={{ width: `${score.diversity_score}%` }}
              />
            </div>
            <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-1">
              {score.metrics.document_count} dokumentów w projekcie
            </p>
          </div>
        </div>

        {/* Score Explanation */}
        <div className="pt-4 border-t border-neutral-200 dark:border-neutral-800">
          <p className="text-xs text-neutral-500 dark:text-neutral-400">
            Wskaźnik jakości uwzględnia częstotliwość przesyłania dokumentów (25%),
            intensywność wyszukiwań (25%), zaangażowanie w czaty (25%)
            oraz różnorodność treści (25%).
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
