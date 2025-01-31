import { useSortStore } from '../sortStore';

describe('sortStore', () => {
  beforeEach(() => {
    useSortStore.setState({
      sortColumn: null,
      sortDirection: 'asc'
    });
  });

  it('should initialize with default state', () => {
    const state = useSortStore.getState();
    expect(state.sortColumn).toBeNull();
    expect(state.sortDirection).toBe('asc');
    expect(state.sortableColumns).toContain('username');
    expect(state.sortableColumns).toContain('last_checked');
  });

  it('should set sort column and direction', () => {
    const { setSort } = useSortStore.getState();
    
    setSort('username', 'desc');
    
    const state = useSortStore.getState();
    expect(state.sortColumn).toBe('username');
    expect(state.sortDirection).toBe('desc');
  });

  it('should toggle sort direction', () => {
    const { setSort, toggleDirection } = useSortStore.getState();
    
    setSort('username', 'asc');
    toggleDirection();
    
    expect(useSortStore.getState().sortDirection).toBe('desc');
    
    toggleDirection();
    expect(useSortStore.getState().sortDirection).toBe('asc');
  });

  it('should reset sort state', () => {
    const { setSort, reset } = useSortStore.getState();
    
    setSort('username', 'desc');
    reset();
    
    const state = useSortStore.getState();
    expect(state.sortColumn).toBeNull();
    expect(state.sortDirection).toBe('asc');
  });

  it('should generate correct query params', () => {
    const { setSort, getQueryParams } = useSortStore.getState();
    
    // No sort column
    expect(getQueryParams()).toEqual({});
    
    // With username sort
    setSort('username', 'desc');
    expect(getQueryParams()).toEqual({
      sort_by: 'username',
      sort_direction: 'desc'
    });
    
    // With niche sort (special case)
    setSort('niche', 'asc');
    expect(getQueryParams()).toEqual({
      sort_by: 'niche__name',
      sort_direction: 'asc'
    });
  });
});