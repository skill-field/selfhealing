import { useState, useEffect, useCallback } from 'react';
import type { Error as AppError, ErrorStats } from '../types';
import { getErrors, getErrorStats } from '../services/api';

interface UseErrorsReturn {
  errors: AppError[];
  loading: boolean;
  error: string | null;
  total: number;
  stats: ErrorStats | null;
  statsLoading: boolean;
  refetch: () => void;
}

export function useErrors(filters?: Record<string, string>): UseErrorsReturn {
  const [errors, setErrors] = useState<AppError[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<ErrorStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);

  const refetch = useCallback(() => {
    setLoading(true);
    setError(null);

    const params: Record<string, string> = {};
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value && value !== 'all') {
          params[key] = value;
        }
      });
    }

    Promise.all([
      getErrors(Object.keys(params).length > 0 ? params : undefined),
      getErrorStats(),
    ])
      .then(([errData, statsData]) => {
        setErrors(errData.errors ?? []);
        setTotal(errData.total ?? 0);
        setStats(statsData);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Failed to fetch errors');
      })
      .finally(() => {
        setLoading(false);
        setStatsLoading(false);
      });
  }, [filters]);

  useEffect(() => {
    refetch();
    const interval = setInterval(refetch, 5000);
    return () => clearInterval(interval);
  }, [refetch]);

  return { errors, loading, error, total, stats, statsLoading, refetch };
}
