import { act } from '@testing-library/react';
import { useFilterStore } from '../filterStore';

describe('filterStore', () => {
  beforeEach(() => {
    act(() => {
      useFilterStore.setState({
        filters: {
          search: '',
          nicheId: null,
          status: null
        }
      });
    });
  });

  it('initializes with default state', () => {
    const state = useFilterStore.getState();
    expect(state.filters).toEqual({
      search: '',
      nicheId: null,
      status: null
    });
  });

  it('sets filter value', () => {
    act(() => {
      useFilterStore.getState().setFilter('search', 'test');
    });
    expect(useFilterStore.getState().filters.search).toBe('test');
  });

  it('resets filters', () => {
    act(() => {
      const store = useFilterStore.getState();
      store.setFilter('search', 'test');
      store.setFilter('nicheId', '123');
      store.setFilter('status', 'active');
      store.resetFilters();
    });

    expect(useFilterStore.getState().filters).toEqual({
      search: '',
      nicheId: null,
      status: null
    });
  });

  describe('getQueryParams', () => {
    it('returns empty object when no filters are set', () => {
      const params = useFilterStore.getState().getQueryParams();
      expect(params).toEqual({});
    });

    it('includes only set filters in params', () => {
      act(() => {
        const store = useFilterStore.getState();
        store.setFilter('search', 'test');
        store.setFilter('nicheId', '123');
        // status remains null
      });

      const params = useFilterStore.getState().getQueryParams();
      expect(params).toEqual({
        search: 'test',
        niche_id: '123'
      });
    });

    it('excludes empty string values', () => {
      act(() => {
        const store = useFilterStore.getState();
        store.setFilter('search', '');
        store.setFilter('nicheId', '123');
      });

      const params = useFilterStore.getState().getQueryParams();
      expect(params).toEqual({
        niche_id: '123'
      });
      expect(params.search).toBeUndefined();
    });

    it('converts nicheId to niche_id in params', () => {
      act(() => {
        useFilterStore.getState().setFilter('nicheId', '123');
      });

      const params = useFilterStore.getState().getQueryParams();
      expect(params.niche_id).toBe('123');
      expect(params.nicheId).toBeUndefined();
    });

    it('handles all filters being set', () => {
      act(() => {
        const store = useFilterStore.getState();
        store.setFilter('search', 'test');
        store.setFilter('nicheId', '123');
        store.setFilter('status', 'active');
      });

      const params = useFilterStore.getState().getQueryParams();
      expect(params).toEqual({
        search: 'test',
        niche_id: '123',
        status: 'active'
      });
    });
  });
});