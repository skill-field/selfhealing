import { useState, useEffect, useCallback } from 'react';
import type { Fix } from '../types';
import { getFixes } from '../services/api';

interface UseFixesReturn {
  fixes: Fix[];
  loading: boolean;
  error: string | null;
  total: number;
  refetch: () => void;
}

export function useFixes(filters?: Record<string, string>): UseFixesReturn {
  const [fixes, setFixes] = useState<Fix[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const filterKey = filters ? JSON.stringify(filters) : '';

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

    getFixes(Object.keys(params).length > 0 ? params : undefined)
      .then((data) => {
        // Handle both array response and object response
        if (Array.isArray(data)) {
          setFixes(data);
          setTotal(data.length);
        } else {
          setFixes(data.fixes ?? []);
          setTotal(data.total ?? (data.fixes?.length ?? 0));
        }
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Failed to fetch fixes');
      })
      .finally(() => {
        setLoading(false);
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterKey]);

  useEffect(() => {
    refetch();
    const interval = setInterval(refetch, 5000);
    return () => clearInterval(interval);
  }, [refetch]);

  return { fixes, loading, error, total, refetch };
}
