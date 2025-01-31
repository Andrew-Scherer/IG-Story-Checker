import { create } from 'zustand';

export const usePaginationStore = create((set, get) => ({
  // State
  currentPage: 1,
  pageSize: 50,
  totalItems: 0,
  loading: false,

  // Actions
  setPage: (page) => {
    set({ currentPage: page });
  },

  setPageSize: (size) => {
    set({ 
      pageSize: size,
      // Reset to first page when changing page size
      currentPage: 1
    });
  },

  setTotalItems: (total) => {
    set({ totalItems: total });
  },

  setLoading: (isLoading) => {
    set({ loading: isLoading });
  },

  // Reset pagination state
  reset: () => {
    set({
      currentPage: 1,
      pageSize: 50,
      totalItems: 0,
      loading: false
    });
  },

  // Computed values
  getTotalPages: () => {
    const { totalItems, pageSize } = get();
    return Math.ceil(totalItems / pageSize);
  },

  // Get params for API requests
  getQueryParams: () => {
    const { currentPage, pageSize } = get();
    return {
      page: currentPage,
      page_size: pageSize
    };
  }
}));