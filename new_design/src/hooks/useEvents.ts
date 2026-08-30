import { apiGet } from '@/lib/api';
import type { Event } from '@/types';
import { useApiListState } from './useApiState';
import type { PaginatedResponse } from './useStartups';

interface ResourceItem {
  resource_id: number;
  title: string;
  description: string | null;
  category: string | null;
  resource_type: string | null;
  url: string | null;
  organization: string | null;
  published_at: string | null;
}

export function useEvents() {
  return useApiListState<Event>(
    () =>
      apiGet<PaginatedResponse<ResourceItem>>('/resources/?category=event').then((res) =>
        res.items.map((r) => ({
          id: String(r.resource_id),
          title: r.title,
          description: r.description || '',
          location: r.organization || '',
          startDate: r.published_at || '',
          endDate: undefined,
          organizer: r.organization || '',
          image: '/news-event.jpg',
          attendees: undefined,
        }))
      ),
    []
  );
}
