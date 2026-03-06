import { useState, useEffect, useCallback } from 'react';
import type { Deployment } from '../types';
import { getDeployments } from '../services/api';

interface UseDeploymentsReturn {
  deployments: Deployment[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useDeployments(): UseDeploymentsReturn {
  const [deployments, setDeployments] = useState<Deployment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(() => {
    setLoading(true);
    setError(null);

    getDeployments()
      .then((data) => {
        if (Array.isArray(data)) {
          setDeployments(data);
        } else {
          setDeployments(data.deployments ?? []);
        }
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Failed to fetch deployments');
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    refetch();
    const interval = setInterval(refetch, 5000);
    return () => clearInterval(interval);
  }, [refetch]);

  return { deployments, loading, error, refetch };
}
