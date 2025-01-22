# Error Logging Process

## Frontend Error Logging

### API Layer (client/src/api/index.js)
```javascript
// Axios interceptors for detailed request/response logging
axiosInstance.interceptors.request.use(
  config => {
    console.log(`=== API Request ===`);
    console.log(`${config.method.toUpperCase()} ${config.url}`);
    console.log('Request headers:', config.headers);
    console.log('Request data:', config.data);
    return config;
  }
);

axiosInstance.interceptors.response.use(
  response => {
    console.log(`=== API Response ===`);
    console.log(`Status: ${response.status}`);
    console.log('Response headers:', response.headers);
    console.log('Response data:', response.data);
    return response;
  },
  error => {
    console.error('!!! API Error !!!');
    console.error('Response status:', error.response?.status);
    console.error('Response headers:', error.response?.headers);
    console.error('Response data:', error.response?.data);
    console.error('Full error object:', error);
    throw error;
  }
);
```

### Store Layer (e.g., client/src/stores/nicheStore.js)
```javascript
try {
  console.log('=== Fetching Niches ===');
  console.log('1. Setting loading state...');
  set({ loading: true, error: null });
  
  console.log('2. Making API request...');
  const response = await niches.list();
  console.log('3. API Response:', response);
  
  console.log('4. Updating store...');
  set({ niches: response });
  console.log('5. Store updated successfully');
} catch (error) {
  console.error('!!! Error fetching niches !!!');
  console.error('Error details:', error);
  console.error('Error message:', error.message);
  console.error('Error stack:', error.stack);
  if (error.response) {
    console.error('Server response:', error.response);
    console.error('Response status:', error.response.status);
    console.error('Response data:', error.response.data);
  }
  set({ error: error.message });
}
```

## Backend Error Logging

### API Routes (e.g., server/api/niche.py)
```python
@niche_bp.route('', methods=['GET'])
def list_niches():
    try:
        current_app.logger.info("=== GET /api/niches ===")
        current_app.logger.info("1. Checking database connection...")
        db.session.execute(text('SELECT 1'))  # Note: Must use SQLAlchemy text() for raw SQL
        
        current_app.logger.info("2. Attempting to fetch ordered niches...")
        niches = Niche.get_ordered()
        current_app.logger.info(f"3. Found {len(niches) if niches else 0} niches")
        
        current_app.logger.info("4. Converting niches to dict...")
        result = [niche.to_dict() for niche in niches]
        current_app.logger.info("5. Successfully converted niches")
        
        return jsonify(result)
    except Exception as e:
        current_app.logger.error("!!! Error in list_niches !!!")
        current_app.logger.error(f"Error type: {type(e).__name__}")
        current_app.logger.error(f"Error message: {str(e)}")
        current_app.logger.error("Full traceback:", exc_info=True)
        db.session.rollback()
        return jsonify({
            'error': str(e),
            'type': type(e).__name__,
            'traceback': traceback.format_exc()
        }), 500
```

## Key Learnings

1. **Step-by-Step Logging**
   - Log each major step in a process with clear numbering
   - Include success/failure indicators for each step
   - Log relevant data at each step (e.g., number of items found)

2. **Error Details**
   - Log error type, message, and full traceback
   - Include relevant context (e.g., function name, endpoint)
   - For API errors, include request/response details

3. **Database Operations**
   - Always use SQLAlchemy's `text()` function for raw SQL
   - Log database connection status
   - Include rollback in error handling

4. **Frontend-Backend Integration**
   - Log both frontend and backend for complete request lifecycle
   - Include request headers and data for debugging CORS/auth issues
   - Track state changes in frontend stores

5. **Common Issues and Solutions**
   - SQLAlchemy raw SQL must use `text()`: `db.session.execute(text('SELECT 1'))`
   - Remember to import `traceback` for Python error formatting
   - Use proper error response format for frontend error handling

## Best Practices

1. **Progressive Logging**
   - Start with high-level operation name
   - Log each step with clear numbering
   - End with success/failure confirmation

2. **Error Context**
   - Include operation name in error logs
   - Log both error summary and details
   - Include stack traces for debugging

3. **Clean Up**
   - Always rollback database sessions on error
   - Clear loading states in frontend
   - Reset error states when retrying operations
