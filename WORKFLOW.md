# System Workflow & Data Flows

## 1. Core Components

### 1.1. Data Models

**Profile**
- Username (primary key)
- Niche association
- Story check statistics
- Last check timestamp
- Last story detection

**Batch**
- ID (UUID)
- Niche association
- Status (queued/in_progress/done)
- Progress tracking
- Creation timestamp
- Associated profiles

**Proxy**
- Connection details
- Health metrics
- Rate limit tracking
- Session management

### 1.2. State Management

**Profile States**
- Story detection status
- Check history
- Niche assignment

**Batch States**
- Queued: Initial state, ready for processing
- In Progress: Currently checking stories
- Done: All profiles processed

**Proxy States**
- Active/Inactive status
- Rate limit tracking
- Error counts
- Session validity

## 2. Interface Workflows

### 2.1. Niche Feed Tab

**Components**
1. Profile List
   - Multi-select functionality
   - Profile statistics display
   - Niche filtering
   - Sort controls

2. File Importer
   - Drag-and-drop support
   - Validation
   - Duplicate handling
   - Error reporting

3. Story Check Controls
   - "Check Selected Profiles" button
   - Selection count display
   - Batch creation trigger

**Actions**
1. Profile Selection
   - Click rows to select
   - Shift-click for range
   - Ctrl/Cmd-click for individual

2. Profile Import
   - Upload text file
   - Parse usernames
   - Validate format
   - Handle duplicates

3. Batch Creation
   - Select profiles
   - Click check button
   - System creates batch
   - Redirect to batch tab

### 2.2. Batch Tab

**Components**
1. Batch Table
   - Multi-select support
   - Progress tracking
   - Status display
   - Success rate calculation

2. Batch Controls
   - Start selected
   - Stop selected
   - Delete selected

**Actions**
1. Batch Management
   - Select batches
   - Start/stop processing
   - Monitor progress
   - View results

2. Results Tracking
   - Success rate display
   - Profile completion count
   - Story detection stats

### 2.3. Settings Tab

**Components**
1. Proxy Management
   - Add/remove proxies
   - Health monitoring
   - Rate limit config
   - Session management

2. System Settings
   - Thread count control
   - Rate limiting
   - Retry configuration
   - Error thresholds

## 3. Processing Workflows

### 3.1. Story Checking

1. **Profile Selection**
   - User selects profiles in Niche Feed
   - System validates selection
   - Creates batch record

2. **Batch Processing**
   - User starts batch
   - System assigns workers
   - Processes profiles sequentially
   - Updates stats in real-time

3. **Resource Management**
   - Just-in-time proxy assignment
   - Session creation/cleanup
   - Rate limit handling
   - Error recovery

### 3.2. Proxy Management

1. **Assignment**
   - Least recently used selection
   - Health verification
   - Rate limit checking
   - Session validation

2. **Monitoring**
   - Success/failure tracking
   - Rate limit detection
   - Error counting
   - Health scoring

3. **Recovery**
   - Automatic retry on failure
   - Rate limit cooldown
   - Session refresh
   - Proxy rotation

## 4. Data Flows

### 4.1. Story Check Flow

1. **Initialization**
   - Create batch record
   - Associate selected profiles
   - Set initial state

2. **Processing**
   - Get available worker
   - Check story status
   - Update profile stats
   - Release worker

3. **Completion**
   - Update final stats
   - Clean up resources
   - Mark batch done

### 4.2. Resource Flow

1. **Worker Assignment**
   - Get from pool
   - Verify health
   - Assign proxy/session
   - Monitor usage

2. **Session Management**
   - Create as needed
   - Track usage
   - Handle expiration
   - Clean up after use

3. **Proxy Rotation**
   - Track usage counts
   - Handle rate limits
   - Manage cooldowns
   - Balance load

## 5. Error Handling

### 5.1. Story Check Errors

1. **Rate Limits**
   - Detection
   - Cooldown period
   - Retry with new proxy
   - Update proxy stats

2. **Network Errors**
   - Automatic retry
   - Proxy rotation
   - Error counting
   - Status preservation

### 5.2. Resource Errors

1. **Proxy Failures**
   - Health check failure
   - Connection timeout
   - Authentication error
   - Rate limit exceeded

2. **Session Errors**
   - Invalid session
   - Expired cookie
   - Login required
   - Session cleanup

## 6. Best Practices

### 6.1. Performance

1. **Resource Usage**
   - Efficient proxy rotation
   - Session reuse when possible
   - Proper cleanup
   - Load balancing

2. **Rate Limiting**
   - Per-proxy tracking
   - Global rate limits
   - Cooldown periods
   - Retry backoff

### 6.2. Reliability

1. **Error Recovery**
   - Automatic retries
   - State preservation
   - Resource cleanup
   - Error logging

2. **Data Consistency**
   - Transaction handling
   - State validation
   - Progress tracking
   - Stats accuracy

## 7. Monitoring

### 7.1. System Health

1. **Metrics**
   - Active batches
   - Worker utilization
   - Proxy health
   - Error rates

2. **Performance**
   - Response times
   - Success rates
   - Resource usage
   - Queue depth

### 7.2. Error Tracking

1. **Logging**
   - Error details
   - Stack traces
   - State information
   - Recovery actions

2. **Analysis**
   - Error patterns
   - Proxy performance
   - Rate limit impact
   - Success rates
