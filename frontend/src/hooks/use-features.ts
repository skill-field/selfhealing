import { useState, useEffect, useCallback } from 'react';
import type { FeatureRequest } from '../types';
import { getFeatures } from '../services/api';

interface UseFeaturesReturn {
  features: FeatureRequest[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useFeatures(statusFilter?: string): UseFeaturesReturn {
  const [features, setFeatures] = useState<FeatureRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(() => {
    setLoading(true);
    setError(null);

    const params: Record<string, string> = {};
    if (statusFilter && statusFilter !== 'all') {
      params.status = statusFilter;
    }

    getFeatures(Object.keys(params).length > 0 ? params : undefined)
      .then((data) => {
        if (Array.isArray(data)) {
          setFeatures(data);
        } else {
          setFeatures(data.features ?? []);
        }
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Failed to fetch features');
      })
      .finally(() => {
        setLoading(false);
      });
  }, [statusFilter]);

  useEffect(() => {
    refetch();
    const interval = setInterval(refetch, 5000);
    return () => clearInterval(interval);
  }, [refetch]);

  return { features, loading, error, refetch };
}
