import { apiGet } from '@/lib/api';
import type { Opportunity } from '@/types';
import { useApiListState } from './useApiState';
import type { PaginatedResponse } from './useStartups';

interface OpportunityApiItem {
  id: string;
  title: string;
  organization: string;
  deadline: string;
  category: string;
  description: string;
}

export function useOpportunities() {
  return useApiListState<Opportunity>(
    () => apiGet<PaginatedResponse<OpportunityApiItem>>('/resources/opportunities').then((res) => res.items),
    []
  );
}
