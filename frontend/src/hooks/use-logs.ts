import { useState, useEffect, useCallback } from 'react';
import type { LogEntry } from '../types';
import { getLogs } from '../services/api';

interface UseLogsReturn {
  logs: LogEntry[];
  loading: boolean;
  error: string | null;
  total: number;
  refetch: () => void;
}

export function useLogs(params?: Record<string, string>): UseLogsReturn {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(() => {
    setLoading(true);
    setError(null);
    getLogs(params)
      .then((data) => {
        setLogs(data.logs ?? []);
        setTotal(data.total ?? 0);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Failed to fetch logs');
      })
      .finally(() => setLoading(false));
  }, [params]);

  useEffect(() => {
    refetch();
    const interval = setInterval(refetch, 5000);
    return () => clearInterval(interval);
  }, [refetch]);

  return { logs, loading, error, total, refetch };
}
