import { useQuery, type UseQueryOptions, type UseQueryResult } from '@tanstack/react-query';
import { useTimeline } from '../hooks/useTimeline';
import { api } from './client';

export function useAegisQuery<T>(
  endpoint: string,
  options?: Omit<UseQueryOptions<T, Error, T, any[]>, 'queryKey' | 'queryFn'>
): UseQueryResult<T, Error> {
  const { asOf } = useTimeline();

  // Append as_of query parameter correctly
  const url = new URL(endpoint, 'http://localhost'); // dummy base just for URL parsing
  if (asOf && asOf !== 'now') {
    url.searchParams.set('as_of', asOf);
  }
  const finalEndpoint = url.pathname + url.search;

  return useQuery<T, Error, T, any[]>({
    queryKey: [endpoint, asOf], // Automatically invalidate/cache based on asOf
    queryFn: () => api.get<T>(finalEndpoint),
    ...options,
  });
}
