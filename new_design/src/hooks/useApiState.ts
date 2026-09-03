import { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';
import { useLanguage } from '@/context/LanguageContext';
import { describeError } from '@/lib/errors';

export interface ApiState<T> {
  data: T | null;
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
}

export function useApiState<T>(fetcher: () => Promise<T>, deps: unknown[] = []): ApiState<T> {
  const { language } = useLanguage();
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const refetch = useCallback(() => setRefreshKey((k) => k + 1), []);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setError(null);
    fetcher()
      .then((result) => {
        if (!cancelled) {
          setData(result);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          // The original error is kept as-is: re-wrapping it in a fresh Error
          // dropped the `kind` the copy layer needs to tell a 500 apart from a
          // sign-in prompt.
          setError(err instanceof Error ? err : new Error(String(err)));
          toast.error(describeError(err, language));
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshKey, ...deps]);

  return { data, isLoading, error, refetch };
}

export interface ApiListState<T> {
  data: T[];
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
}

export function useApiListState<T>(
  fetcher: () => Promise<T[]>,
  deps: unknown[] = []
): ApiListState<T> {
  const { language } = useLanguage();
  const [data, setData] = useState<T[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const refetch = useCallback(() => setRefreshKey((k) => k + 1), []);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setError(null);
    fetcher()
      .then((result) => {
        if (!cancelled) {
          setData(result ?? []);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          // The original error is kept as-is: re-wrapping it in a fresh Error
          // dropped the `kind` the copy layer needs to tell a 500 apart from a
          // sign-in prompt.
          setError(err instanceof Error ? err : new Error(String(err)));
          toast.error(describeError(err, language));
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshKey, ...deps]);

  return { data, isLoading, error, refetch };
}
