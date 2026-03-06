import { useState, useEffect, useCallback } from 'react';
import type { AuditEntry } from '../types';
import { getAuditLog } from '../services/api';

interface UseAuditLogReturn {
  entries: AuditEntry[];
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useAuditLog(): UseAuditLogReturn {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const data = await getAuditLog();
      setEntries(data.entries || []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch audit log');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, [fetchData]);

  return { entries, loading, error, refetch: fetchData };
}
