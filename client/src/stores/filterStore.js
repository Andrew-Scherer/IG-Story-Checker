import { create } from 'zustand';

export const useFilterStore = create((set, get) => ({
  filters: {
    search: '',
    nicheId: null,
    status: null
  },

  setFilter: (key, value) => set(state => ({
    filters: { ...state.filters, [key]: value }
  })),

  resetFilters: () => set({
    filters: { search: '', nicheId: null, status: null }
  }),

  // Convert filters to API query parameters
  getQueryParams: () => {
    const { filters } = get();
    const params = {};

    // Only include non-empty values
    if (filters.search) {
      params.search = filters.search;
    }

    if (filters.nicheId) {
      params.niche_id = filters.nicheId;
    }

    if (filters.status) {
      params.status = filters.status;
    }

    return params;
  }
}));