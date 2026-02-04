/**
 * TrendChart Component
 * Line chart visualization for activity trends over time
 */

import { useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import type { DailyMetric } from '@/types/api';

interface TrendChartProps {
  data: DailyMetric[];
  height?: number;
  showDocuments?: boolean;
  showSearches?: boolean;
  showMessages?: boolean;
  showInsights?: boolean;
}

interface TooltipPayload {
  name: string;
  value: number;
  color: string;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: TooltipPayload[];
  label?: string;
}

// Custom tooltip component defined outside to avoid re-creation on each render
const CustomTooltip = ({ active, payload, label }: CustomTooltipProps) => {
  if (!active || !payload || payload.length === 0) return null;

  return (
    <div className="bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-lg shadow-lg p-3">
      <p className="font-medium text-neutral-900 dark:text-neutral-50 mb-2">
        {label}
      </p>
      {payload.map((entry) => (
        <div key={entry.name} className="flex items-center gap-2 text-sm">
          <div
            className="w-3 h-3 rounded"
            style={{ backgroundColor: entry.color }}
          />
          <span className="text-neutral-600 dark:text-neutral-400">
            {entry.name === 'documents' && 'Dokumenty'}
            {entry.name === 'searches' && 'Wyszukiwania'}
            {entry.name === 'messages' && 'Wiadomości'}
            {entry.name === 'insights' && 'Insighty'}
          </span>
          <span className="font-medium text-neutral-900 dark:text-neutral-50 ml-auto">
            {entry.value}
          </span>
        </div>
      ))}
    </div>
  );
};

export function TrendChart({
  data,
  height = 300,
  showDocuments = true,
  showSearches = true,
  showMessages = true,
  showInsights = false,
}: TrendChartProps) {
  // Format data for recharts
  const chartData = useMemo(() => {
    return data.map((metric) => ({
      date: new Date(metric.date).toLocaleDateString('pl-PL', {
        month: 'short',
        day: 'numeric',
      }),
      documents: metric.documents_uploaded,
      searches: metric.searches_performed,
      messages: metric.chat_messages_sent,
      insights: metric.insights_generated,
    }));
  }, [data]);

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart
        data={chartData}
        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
      >
        <CartesianGrid
          strokeDasharray="3 3"
          className="stroke-neutral-200 dark:stroke-neutral-700"
        />
        <XAxis
          dataKey="date"
          className="text-xs fill-neutral-600 dark:fill-neutral-400"
          tick={{ fill: 'currentColor' }}
        />
        <YAxis
          className="text-xs fill-neutral-600 dark:fill-neutral-400"
          tick={{ fill: 'currentColor' }}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend
          wrapperStyle={{
            paddingTop: '20px',
          }}
          formatter={(value: string) => {
            if (value === 'documents') return 'Dokumenty';
            if (value === 'searches') return 'Wyszukiwania';
            if (value === 'messages') return 'Wiadomości';
            if (value === 'insights') return 'Insighty';
            return value;
          }}
        />
        {showDocuments && (
          <Line
            type="monotone"
            dataKey="documents"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
          />
        )}
        {showSearches && (
          <Line
            type="monotone"
            dataKey="searches"
            stroke="#10b981"
            strokeWidth={2}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
          />
        )}
        {showMessages && (
          <Line
            type="monotone"
            dataKey="messages"
            stroke="#f59e0b"
            strokeWidth={2}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
          />
        )}
        {showInsights && (
          <Line
            type="monotone"
            dataKey="insights"
            stroke="#8b5cf6"
            strokeWidth={2}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
          />
        )}
      </LineChart>
    </ResponsiveContainer>
  );
}
