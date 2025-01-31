# Filter Architecture

## Overview

The Instagram Story Checker uses a centralized filtering system that works in conjunction with server-side pagination to provide efficient data management and consistent user experience across all views.

## Components

### 1. State Management

#### Filter Store (filterStore.js)
```javascript
const useFilterStore = create((set) => ({
  filters: {
    search: '',
    nicheId: null,
    status: null
  },
  setFilter: (key, value) => set(state => ({
    filters: { ...state.filters, [key]: value }
  }))
}));
```

#### Pagination Store (paginationStore.js)
```javascript
const usePaginationStore = create((set) => ({
  currentPage: 1,
  pageSize: 50,
  totalItems: 0,
  setPage: (page) => set({ currentPage: page }),
  setPageSize: (size) => set({ pageSize: size, currentPage: 1 })
}));
```

### 2. Integration Points

#### Profile Store Integration
```javascript
const fetchProfiles = async () => {
  const filterParams = useFilterStore.getState().getQueryParams();
  const paginationParams = usePaginationStore.getState().getQueryParams();
  
  const response = await profiles.list({
    ...filterParams,
    ...paginationParams
  });
  
  usePaginationStore.getState().setTotalItems(response.total);
  set({ profiles: response.profiles });
};
```

### 3. Filter-Pagination Interaction

1. **Filter Changes**
   - When filters are updated, pagination resets to page 1
   - Total item count is updated based on filtered results
   - Page size remains unchanged

2. **Pagination Changes**
   - Current filters are maintained when changing pages
   - Page size changes trigger a reset to page 1
   - Total pages recalculated based on filtered count

## Data Flow

1. **User Input**
   ```
   User Action → Filter Update → Reset Page → Fetch Data
   ```

2. **API Request**
   ```
   Combine Filters & Pagination → API Call → Update UI
   ```

3. **Response Handling**
   ```
   API Response → Update Stores → Update UI Components
   ```

## Implementation Details

### 1. Filter Types

- **Text Search**: Username search with server-side filtering
- **Niche Filter**: Filter by niche ID
- **Status Filter**: Active/Inactive status filtering

### 2. Pagination Controls

- **Page Navigation**: First, Previous, Next, Last
- **Page Size**: 25, 50, 100 items per page
- **Direct Page Input**: Jump to specific page

### 3. Server Integration

#### API Parameters
```javascript
{
  search: string,
  niche_id: number,
  status: string,
  page: number,
  page_size: number
}
```

#### Response Format
```javascript
{
  profiles: Profile[],
  total: number,
  page: number,
  page_size: number
}
```

## Component Usage

### 1. Master List
```jsx
function MasterList() {
  const { filters, setFilter } = useFilterStore();
  const { setPage } = usePaginationStore();

  // Reset pagination when filters change
  const handleFilterChange = (key, value) => {
    setFilter(key, value);
    setPage(1);
  };
}
```

### 2. Profile List
```jsx
function ProfileList({ nicheId }) {
  const { setFilter } = useFilterStore();
  const { reset: resetPagination } = usePaginationStore();

  useEffect(() => {
    setFilter('nicheId', nicheId);
    resetPagination();
  }, [nicheId]);
}
```

## Best Practices

1. **Filter Changes**
   - Always reset to page 1 when filters change
   - Maintain filter state during navigation
   - Clear filters with reset function

2. **Pagination**
   - Use server-side pagination for large datasets
   - Maintain reasonable page sizes
   - Show loading states during transitions

3. **Performance**
   - Debounce text search inputs
   - Cache filtered results when appropriate
   - Use optimistic UI updates

## Error Handling

1. **Invalid Filters**
   - Validate filter values before API calls
   - Provide user feedback for invalid filters
   - Reset to default state on error

2. **Pagination Errors**
   - Handle out-of-range page numbers
   - Fallback to first page on errors
   - Maintain last valid state

## Testing

1. **Unit Tests**
   - Test filter state management
   - Verify pagination calculations
   - Check store interactions

2. **Integration Tests**
   - Test filter-pagination interaction
   - Verify API parameter generation
   - Check response handling

3. **Component Tests**
   - Test UI interactions
   - Verify filter updates
   - Check pagination controls