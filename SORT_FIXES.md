# Sorting System Fixes

## Current Issues

### 1. Frontend-Backend Column Mapping
- Frontend uses 'stats' for Story Detection Rate column
- Backend has no direct 'stats' column
- Need to map frontend columns to actual database fields

### 2. Query Builder Issues
- Pagination correctly applied after sorting
- Missing support for calculated fields (like detection rate)
- DateTime handling needs timezone awareness
- No validation for sort columns

### 3. Special Cases Not Handled
- Only 'niche' special case is handled
- Detection rate needs to sort by (total_detections / total_checks)
- DateTime columns need proper NULL handling with timezones

## Implementation Plan

### Phase 1: Frontend Column Mapping
1. Update sortStore.js:
```javascript
const COLUMN_MAPPING = {
  'stats': 'detection_rate',
  'niche': 'niche__name',
  // other columns map 1:1
};
```

### Phase 2: Query Builder Enhancements
1. Add support for calculated fields:
```python
CALCULATED_FIELDS = {
    'detection_rate': lambda model: (
        func.cast(model.total_detections, Float) / 
        func.cast(model.total_checks, Float) * 100
    )
}
```

2. Improve datetime handling:
```python
def get_order_column(self, column_name):
    column = getattr(self.model, column_name)
    if isinstance(column.type, DateTime):
        return func.coalesce(column, 
            datetime.max if self.sort_direction == 'asc' 
            else datetime.min)
    return column
```

### Phase 3: API Layer Validation
1. Add column validation in profile API:
```python
VALID_SORT_COLUMNS = {
    'username', 'status', 'last_checked',
    'last_detected', 'detection_rate', 'niche__name'
}
```

2. Transform sort parameters:
```python
def transform_sort_params(sort_by, direction):
    if sort_by not in VALID_SORT_COLUMNS:
        raise ValueError(f"Invalid sort column: {sort_by}")
    return sort_by, direction
```

## Testing Strategy

1. Unit Tests:
- Test column mapping in sortStore
- Test query builder with calculated fields
- Test datetime sorting with NULL values
- Test API parameter validation

2. Integration Tests:
- Test sorting across pages
- Test sorting with filters
- Test special case sorting (detection rate, niche)

3. E2E Tests:
- Test sorting persistence
- Test sorting with large datasets
- Test sorting with all column types

## Migration Steps

1. Deploy Backend Changes:
- Update query builder
- Add column validation
- Add calculated fields support

2. Deploy Frontend Changes:
- Update column mapping
- Update MasterList component
- Update sortStore configuration

3. Verification:
- Check sorting works across pages
- Verify correct handling of NULL values
- Confirm detection rate sorting works
- Test timezone handling