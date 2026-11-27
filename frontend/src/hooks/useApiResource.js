import { useCallback, useEffect, useState } from 'react';

export function useApiResource(fetcher) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    setData(null);
    try {
      setData(await fetcher());
    } catch (err) {
      setError(err?.message || 'Failed to load data from FastAPI.');
    } finally {
      setLoading(false);
    }
  }, [fetcher]);

  useEffect(() => {
    load();
  }, [load]);

  return {
    data,
    setData,
    loading,
    error,
    setError,
    reload: load,
  };
}
