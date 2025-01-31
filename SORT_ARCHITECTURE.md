# Sorting Architecture Analysis

## Current Implementation Issues

### 1. Duplicate Sort Logic
- Table.jsx has internal sorting logic (lines 40-78) that's not being used when external sorting is provided
- Both MasterList and ProfileList maintain their own sort state
- Redundant sort parameter handling across components

### 2. Mixed Client/Server Sorting
- Table component has client-side sorting capability (sortedData useMemo)
- MasterList uses server-side sorting (fetchProfiles with sort params)
- This creates confusion about where sorting actually happens

### 3. Inconsistent Sort State Management
- MasterList.jsx manages sort state locally (lines 32-33):
```javascript
const [sortColumn, setSortColumn] = useState(null);
const [sortDirection, setSortDirection] = useState('asc');
```
- Sort state resets on component unmount/remount
- No persistence between page refreshes

### 4. Complex Column Configuration
- Column definitions include sorting logic mixed with display logic
- Sortable columns defined individually in each component
- No central management of sortable fields

### 5. Performance Issues
- Each sort triggers a new API request
- No caching of sorted results
- Unnecessary re-renders due to local sort state

## Implementation Roadmap

### Phase 1: Core Sort Store (Critical)
**Goal**: Establish centralized sort state management
- [ ] Create sortStore.js with basic state and actions
- [ ] Add TypeScript definitions for sort types
- [ ] Implement getQueryParams for API integration
- [ ] Add tests for sortStore
- [ ] Update profileStore to use sortStore

### Phase 2: Table Component Refactor (Critical)
**Goal**: Remove client-side sorting and use server-side only
- [ ] Remove internal sorting logic from Table component
- [ ] Add sort store integration to Table
- [ ] Update sort indicators in Table
- [ ] Remove sortedData useMemo
- [ ] Update Table component tests
- [ ] Add loading state during sort operations

### Phase 3: List Component Updates (High)
**Goal**: Standardize sorting across all list views
- [ ] Remove local sort state from MasterList
- [ ] Remove local sort state from ProfileList
- [ ] Update both components to use sortStore
- [ ] Add sort-related tests for both components
- [ ] Ensure consistent sort behavior

### Phase 4: Column Configuration (Medium)
**Goal**: Centralize column definitions and sort configuration
- [ ] Create types/columns.ts for column definitions
- [ ] Move column configs to separate files
- [ ] Update components to use centralized columns
- [ ] Add validation for sortable columns
- [ ] Update documentation

### Phase 5: Testing & Documentation (Medium)
**Goal**: Ensure reliability and maintainability
- [ ] Add integration tests for sorting
- [ ] Add E2E tests for sort workflow
- [ ] Update API documentation
- [ ] Add sorting examples to docs
- [ ] Create migration guide

## Benefits

1. **Consistency**
   - Single source of truth for sort state
   - Consistent behavior across components
   - Predictable sorting experience

2. **Performance**
   - Reduced API calls
   - Better state management
   - Optimized re-renders

3. **Maintainability**
   - Centralized sort logic
   - Easier testing
   - Clear separation of concerns

4. **User Experience**
   - Consistent sort indicators
   - Better feedback on sort operations
   - Reliable sorting behavior

## Migration Strategy

1. **Preparation**
   - Add sort store
   - Update tests
   - Document changes

2. **Component Updates**
   - Update Table component
   - Remove local sort state
   - Add store integration

3. **Testing**
   - Unit tests for store
   - Integration tests
   - E2E tests for sorting

4. **Rollout**
   - Deploy changes
   - Monitor performance
   - Gather feedback