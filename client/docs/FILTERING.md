# Profile Filtering System

## Overview
The IG Story Checker uses a centralized filtering system built with Zustand. This system provides a single source of truth for all profile filtering operations across the application, ensuring consistent behavior between different views.

## Architecture

### Filter Store (`src/stores/filterStore.js`)
The core of the filtering system is a Zustand store that manages all filter state:

```javascript
const useFilterStore = create((set) => ({
  filters: {
    search: '',      // Text search for usernames
    nicheId: null,   // Selected niche filter
    status: null     // Profile status filter (active/inactive)
  },
  setFilter: (key, value) => set(state => ({
    filters: { ...state.filters, [key]: value }
  })),
  resetFilters: () => set({
    filters: { search: '', nicheId: null, status: null }
  })
}));
```

### Integration with Profile Store (`src/stores/profileStore.js`)
The profile store uses the filter store to fetch filtered data:
```javascript
const useProfileStore = create((set, get) => ({
  fetchProfiles: async () => {
    const filters = useFilterStore.getState().filters;
    const params = {
      search: filters.search || undefined,
      niche_id: filters.nicheId || undefined,
      status: filters.status || undefined
    };
    // Fetch profiles with filter params...
  }
}));
```

## Component Usage

### NicheFeed Component
```javascript
const NicheFeed = () => {
  const { setFilter } = useFilterStore();
  
  // Filter by niche when selected
  const handleNicheClick = (nicheId) => {
    setFilter('nicheId', nicheId);
    fetchProfiles();
  };
};
```

### MasterList Component
```javascript
const MasterList = () => {
  const { filters, setFilter } = useFilterStore();
  
  // Search filter
  <input
    value={filters.search}
    onChange={e => setFilter('search', e.target.value)}
  />
  
  // Status filter
  <select
    value={filters.status}
    onChange={e => setFilter('status', e.target.value)}
  >
    <option value="">All Status</option>
    <option value="active">Active</option>
    <option value="inactive">Inactive</option>
  </select>
};
```

## Filter Synchronization
- Filters are automatically synchronized between NicheFeed and MasterList views
- Changes in one component immediately reflect in all other components
- Filter state persists during navigation between views

## Testing
The filtering system includes comprehensive tests:
- Unit tests for the filter store (`filterStore.test.js`)
- Integration tests for components (`ProfileList.test.jsx`, `MasterList.test.jsx`)
- Tests cover filter operations, synchronization, and edge cases

## API Integration
The filtering system integrates with the backend API through query parameters:
- `search`: Text search for usernames
- `niche_id`: Filter by specific niche
- `status`: Filter by profile status

## Best Practices
1. Always use the filter store for filter operations
2. Update filters through the `setFilter` action
3. Reset filters when needed using `resetFilters`
4. Fetch new data after filter changes
5. Handle loading and error states appropriately

## Migration from Old System
The previous filtering system using `filterUtils.js` has been deprecated in favor of this centralized approach. Benefits of the new system include:
- Single source of truth for filter state
- Simplified component code
- Better state management
- Improved maintainability
- Consistent behavior across views