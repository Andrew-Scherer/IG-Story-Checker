import { act } from '@testing-library/react';
import { usePaginationStore } from '../paginationStore';

describe('paginationStore', () => {
  beforeEach(() => {
    act(() => {
      usePaginationStore.setState({
        currentPage: 1,
        pageSize: 50,
        totalItems: 0,
        loading: false
      });
    });
  });

  it('initializes with default state', () => {
    const state = usePaginationStore.getState();
    expect(state.currentPage).toBe(1);
    expect(state.pageSize).toBe(50);
    expect(state.totalItems).toBe(0);
    expect(state.loading).toBe(false);
  });

  it('sets page correctly', () => {
    act(() => {
      usePaginationStore.getState().setPage(2);
    });
    expect(usePaginationStore.getState().currentPage).toBe(2);
  });

  it('sets page size and resets to first page', () => {
    act(() => {
      usePaginationStore.getState().setPage(2);
      usePaginationStore.getState().setPageSize(25);
    });
    const state = usePaginationStore.getState();
    expect(state.pageSize).toBe(25);
    expect(state.currentPage).toBe(1); // Should reset to first page
  });

  it('sets total items', () => {
    act(() => {
      usePaginationStore.getState().setTotalItems(100);
    });
    expect(usePaginationStore.getState().totalItems).toBe(100);
  });

  it('sets loading state', () => {
    act(() => {
      usePaginationStore.getState().setLoading(true);
    });
    expect(usePaginationStore.getState().loading).toBe(true);
  });

  it('calculates total pages correctly', () => {
    act(() => {
      const store = usePaginationStore.getState();
      store.setPageSize(10);
      store.setTotalItems(95);
    });
    expect(usePaginationStore.getState().getTotalPages()).toBe(10);
  });

  it('gets query params', () => {
    act(() => {
      const store = usePaginationStore.getState();
      store.setPage(3);
      store.setPageSize(25);
    });
    
    const params = usePaginationStore.getState().getQueryParams();
    expect(params).toEqual({
      page: 3,
      page_size: 25
    });
  });

  it('resets state', () => {
    act(() => {
      const store = usePaginationStore.getState();
      store.setPage(3);
      store.setPageSize(25);
      store.setTotalItems(100);
      store.setLoading(true);
      store.reset();
    });

    const state = usePaginationStore.getState();
    expect(state.currentPage).toBe(1);
    expect(state.pageSize).toBe(50);
    expect(state.totalItems).toBe(0);
    expect(state.loading).toBe(false);
  });
});