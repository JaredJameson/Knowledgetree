import React, { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import type { SubscriptionDetails, SubscriptionPlan } from '../types/subscription';
import api from '../lib/api';
import { useAuth } from './AuthContext';

interface UsageMetric {
  used: number;
  limit: number | null;
  remaining: number | null;
  allowed: boolean;
}

interface UsageLimits {
  plan: SubscriptionPlan;
  messages: UsageMetric;
  documents: UsageMetric;
  storage: UsageMetric;
  projects: UsageMetric;
}

interface SubscriptionContextType {
  subscription: SubscriptionDetails | null;
  usage: UsageLimits | null;
  loading: boolean;
  error: string | null;
  isDemoMode: boolean;
  refreshSubscription: () => Promise<void>;
  refreshUsage: () => Promise<void>;
  isLimitReached: (metric: keyof Pick<UsageLimits, 'messages' | 'documents' | 'storage' | 'projects'>) => boolean;
  getUsagePercentage: (metric: keyof Pick<UsageLimits, 'messages' | 'documents' | 'storage' | 'projects'>) => number;
  canUpload: boolean;
  canSendMessage: boolean;
}

const SubscriptionContext = createContext<SubscriptionContextType | undefined>(undefined);

interface SubscriptionProviderProps {
  children: ReactNode;
}

export const SubscriptionProvider: React.FC<SubscriptionProviderProps> = ({ children }) => {
  const { isAuthenticated } = useAuth();
  const [subscription, setSubscription] = useState<SubscriptionDetails | null>(null);
  const [usage, setUsage] = useState<UsageLimits | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDemoMode, setIsDemoMode] = useState(false);

  const refreshSubscription = async () => {
    try {
      const response = await api.get('/subscriptions/my-subscription');
      setSubscription(response.data);
      setIsDemoMode(response.data.is_demo || false);
      setError(null);
    } catch (err: any) {
      console.error('Failed to fetch subscription:', err);
      setError(err.response?.data?.detail || 'Failed to load subscription');
    }
  };

  const refreshUsage = async () => {
    try {
      const response = await api.get('/usage/limits');
      setUsage(response.data);
      setError(null);
    } catch (err: any) {
      console.error('Failed to fetch usage:', err);
      setError(err.response?.data?.detail || 'Failed to load usage data');
    }
  };

  const fetchData = async () => {
    setLoading(true);
    await Promise.all([refreshSubscription(), refreshUsage()]);
    setLoading(false);
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchData();
    } else {
      // User not authenticated - set loading to false
      setLoading(false);
      setSubscription(null);
      setUsage(null);
      setError(null);
    }
  }, [isAuthenticated]);

  const isLimitReached = (metric: keyof Pick<UsageLimits, 'messages' | 'documents' | 'storage' | 'projects'>): boolean => {
    if (!usage) return false;
    const metricData = usage[metric];
    return !metricData.allowed;
  };

  const getUsagePercentage = (metric: keyof Pick<UsageLimits, 'messages' | 'documents' | 'storage' | 'projects'>): number => {
    if (!usage) return 0;
    const metricData = usage[metric];

    // If unlimited (limit is null), return 0%
    if (metricData.limit === null) return 0;

    // Calculate percentage
    return Math.min(100, Math.round((metricData.used / metricData.limit) * 100));
  };

  const canUpload = !isLimitReached('documents') && !isLimitReached('storage');
  const canSendMessage = !isLimitReached('messages');

  const value: SubscriptionContextType = {
    subscription,
    usage,
    loading,
    error,
    isDemoMode,
    refreshSubscription,
    refreshUsage,
    isLimitReached,
    getUsagePercentage,
    canUpload,
    canSendMessage,
  };

  return (
    <SubscriptionContext.Provider value={value}>
      {children}
    </SubscriptionContext.Provider>
  );
};

export const useSubscription = (): SubscriptionContextType => {
  const context = useContext(SubscriptionContext);
  if (context === undefined) {
    throw new Error('useSubscription must be used within a SubscriptionProvider');
  }
  return context;
};
