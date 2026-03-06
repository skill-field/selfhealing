import { useState, useEffect, useCallback } from 'react';
import type { DashboardSummary, DashboardTimeline } from '../types';
import { getDashboardSummary, getDashboardTimeline } from '../services/api';

interface UseDashboardReturn {
  summary: DashboardSummary | null;
  timeline: DashboardTimeline | null;
  loading: boolean;
  error: string | null;
}

export function useDashboard(): UseDashboardReturn {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [timeline, setTimeline] = useState<DashboardTimeline | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const [s, t] = await Promise.all([
        getDashboardSummary(),
        getDashboardTimeline(),
      ]);
      setSummary(s);
      setTimeline(t);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch dashboard data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, [fetchData]);

  return { summary, timeline, loading, error };
}
