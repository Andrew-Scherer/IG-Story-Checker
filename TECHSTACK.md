# Tech Stack for Instagram Story-Checking Tool

## Tech Stack Overview

### Backend
- **Framework**: Flask
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Libraries/Extensions**:
  - Flask-SQLAlchemy (database management)
  - Flask-Migrate (database migrations)

### Frontend
- **Framework**: React
- **State Management**: Zustand
- **Styling**: SCSS modules

## Testing Strategy

### Backend Testing (pytest)
- **Framework**: pytest
- **Key Components**:
  1. **Unit Tests**:
     - API endpoints
     - Worker management
     - Database models
     - Batch processing
  
  2. **Integration Tests**:
     - Complete batch workflows
     - Worker pool management
     - Database operations
  
  3. **Fixtures**:
     - Database fixtures
     - Mock workers
     - Test data
  
  4. **Test Coverage**:
     - pytest-cov for coverage reporting
     - Comprehensive error case testing

### Frontend Testing
- **Framework**: Jest + React Testing Library
- **Key Components**:
  1. **Unit Tests**:
     - React components
     - Store actions
     - API client
  
  2. **Integration Tests**:
     - Component interactions
     - Store integration
     - API integration

## Implementation Plan

### 1. Flask Backend

#### Features
1. **Niche Management**:
   - CRUD endpoints
   - Profile organization
   - Error handling

2. **Profile Management**:
   - Profile CRUD operations
   - Multi-select functionality
   - Import from files
   - Stats tracking

3. **Batch Management**:
   - Creation from selected profiles
   - Progress monitoring
   - Start/stop functionality
   - Batch deletion with cleanup

4. **Worker Management**:
   - Worker pool management
   - Proxy assignment
   - Session handling
   - Rate limiting

#### Testing Implementation
```python
# Example test structure
def test_batch_workflow():
    # Create batch with selected profiles
    response = client.post('/api/batches', json={
        'niche_id': niche.id,
        'profile_ids': [profile1.id, profile2.id]
    })
    assert response.status_code == 201
    batch_id = response.json['id']
    
    # Start batch
    response = client.post('/api/batches/start', json={
        'batch_ids': [batch_id]
    })
    assert response.status_code == 200
    
    # Verify completion
    response = client.get('/api/batches')
    batch = next(b for b in response.json if b['id'] == batch_id)
    assert batch['status'] == 'done'
```

### 2. React Frontend

#### Components
1. **Common Components**:
   - Table (multi-select, sorting)
   - Button (loading states)
   - Modal (confirmations)

2. **Feature Components**:
   - NicheFeed (profile management)
   - BatchTable (batch operations)
   - ProxyManager (proxy configuration)

#### Testing Implementation
```javascript
// Example component test
describe('BatchTable', () => {
  it('handles batch selection', () => {
    render(<BatchTable batches={mockBatches} />);
    const row = screen.getByText(mockBatches[0].id);
    fireEvent.click(row);
    expect(row).toHaveClass('selected');
  });

  it('handles batch actions', async () => {
    const onStart = jest.fn();
    render(<BatchTable onStart={onStart} />);
    fireEvent.click(screen.getByText('Start Selected'));
    expect(onStart).toHaveBeenCalled();
  });
});
```

### 3. State Management (Zustand)

#### Stores
1. **Batch Store**:
```javascript
{
  batches: [],           // Current batches
  loading: false,        // Loading state
  error: null,          // Error state
  actions: {
    fetchBatches,      // Get all batches
    createBatch,       // Create from selected profiles
    startBatches,      // Start selected batches
    stopBatches,       // Stop selected batches
    deleteBatches      // Delete selected batches
  }
}
```

2. **Profile Store**:
```javascript
{
  profiles: [],
  selectedProfiles: [],
  loading: false,
  error: null,
  actions: {
    fetchProfiles,
    importProfiles,
    selectProfile,
    selectRange
  }
}
```

#### Testing Approach
```javascript
// Example store test
describe('batchStore', () => {
  it('creates batch from selected profiles', async () => {
    const store = useBatchStore();
    await store.createBatch({
      niche_id: 1,
      profile_ids: [1, 2, 3]
    });
    expect(store.batches).toHaveLength(1);
    expect(store.batches[0].status).toBe('queued');
  });
});
```

## Development Workflow

### 1. Test-Driven Development
1. Write failing test
2. Implement feature
3. Pass test
4. Refactor
5. Repeat

### 2. Code Review Process
- Test coverage requirements
- Code style enforcement
- Documentation updates

## Deployment

### Backend
- Flask development server
- PostgreSQL database
- Worker pool management

### Frontend
- React development server
- API integration
- State management

## Performance Considerations

### Backend
1. **Worker Management**:
   - Efficient proxy rotation
   - Session reuse
   - Rate limit handling

2. **Database Operations**:
   - Batch operations
   - Efficient queries
   - Transaction management

### Frontend
1. **State Management**:
   - Optimistic updates
   - Error recovery
   - Loading states

2. **UI Performance**:
   - Efficient rendering
   - Pagination
   - Error boundaries

## Why This Stack?

1. **Simplicity**:
   - Clear component structure
   - Straightforward state management
   - Easy testing

2. **Reliability**:
   - Comprehensive error handling
   - Transaction safety
   - Resource management

3. **Maintainability**:
   - Clear separation of concerns
   - Well-tested codebase
   - Good documentation

4. **Developer Experience**:
   - Fast feedback loop
   - Good debugging tools
   - Easy local development

This tech stack provides a robust foundation for building a reliable and maintainable Instagram Story-checking tool with comprehensive testing coverage.
