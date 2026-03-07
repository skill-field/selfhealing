import { useEffect, useRef, useState, useCallback } from 'react';
import type { SSEEvent } from '../types';

const SSE_URL = '/api/v1/events/stream';
const MAX_BACKOFF = 30000;

export function useSSE() {
  const [connected, setConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState<SSEEvent | null>(null);
  const [events, setEvents] = useState<SSEEvent[]>([]);
  const retryCount = useRef(0);
  const esRef = useRef<EventSource | null>(null);

  const connect = useCallback(() => {
    if (esRef.current) {
      esRef.current.close();
    }

    const es = new EventSource(SSE_URL);
    esRef.current = es;

    es.onopen = () => {
      setConnected(true);
      retryCount.current = 0;
    };

    // Handle unnamed messages
    es.onmessage = (event) => {
      try {
        const parsed: SSEEvent = JSON.parse(event.data);
        setLastEvent(parsed);
        setEvents((prev) => [...prev.slice(-99), parsed]);
      } catch {
        // ignore non-JSON messages
      }
    };

    // Handle named event types (server sends event: <type>)
    const eventTypes = [
      'error_detected', 'classification_done', 'fix_generated',
      'fix_approved', 'fix_rejected', 'deployment_status',
      'feature_status', 'feature_generated', 'feature_approved',
      'feature_rejected', 'heartbeat',
    ];
    for (const type of eventTypes) {
      es.addEventListener(type, (event: MessageEvent) => {
        try {
          const parsed: SSEEvent = JSON.parse(event.data);
          if (type === 'heartbeat') return; // skip heartbeats
          setLastEvent(parsed);
          setEvents((prev) => [...prev.slice(-99), parsed]);
        } catch {
          // ignore
        }
      });
    }

    es.onerror = () => {
      es.close();
      setConnected(false);
      const delay = Math.min(1000 * 2 ** retryCount.current, MAX_BACKOFF);
      retryCount.current += 1;
      setTimeout(connect, delay);
    };
  }, []);

  useEffect(() => {
    connect();
    return () => {
      esRef.current?.close();
    };
  }, [connect]);

  return { connected, lastEvent, events };
}
