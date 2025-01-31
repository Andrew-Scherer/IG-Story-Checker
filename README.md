# Instagram Story Checker

A tool designed to efficiently check and monitor Instagram stories across multiple profiles. The system uses a niche-based organization system with robust batch processing capabilities.

## 1. Overview

Core functionality:
- **Profile Management**: Import and organize Instagram profiles
- **Batch Processing**: Check stories across multiple profiles
- **Progress Monitoring**: Track story detection results
- **Resource Management**: Efficient proxy and session handling
- **Advanced Filtering**: Centralized filtering system across views ([see FILTERING.md](client/docs/FILTERING.md))
- **Server-Side Pagination**: Efficient data loading and navigation ([see PAGINATION.md](client/docs/PAGINATION.md))

## 2. Interface

### 2.1. Niche Feed Tab

**Purpose**: Manage profiles and initiate story checks.

**Features**:
1. **Profile List**
   - Multi-select functionality
   - Profile statistics display
   - Synchronized filtering with Master List
   - Server-side pagination
   - Sort controls

2. **File Importer**
   - Drag-and-drop support
   - Username validation
   - Duplicate handling
   - Error reporting

3. **Story Check Controls**
   - "Check Selected Profiles" button
   - Selection count display
   - Batch creation trigger

### 2.2. Batch Tab

**Purpose**: Monitor and control batch processing.

**Features**:
1. **Batch Table**
   - Multi-select support
   - Progress tracking
   - Status display
   - Success rate calculation

2. **Batch Controls**
   - Start selected batches
   - Stop selected batches
   - Delete selected batches
   - Refresh button to update batch status and progress

3. **Status Tracking**
   - Queued batches
   - In-progress batches
   - Completed batches
   - Error states

4. **Real-time Updates**
   - Manual refresh option to update batch status, progress, and queue positions without page reload

### 2.3. Settings Tab

**Purpose**: System configuration and proxy management.

**Features**:
1. **Proxy Management**
   - Add/remove proxies
   - Health monitoring
   - Rate limit configuration
   - Session management

2. **System Settings**
   - Thread count control
   - Rate limiting
   - Retry configuration
   - Error thresholds

## 3. Core Workflows

### 3.1. Profile Selection & Batch Creation

1. **Select Profiles**
   - Navigate to Niche Feed
   - Use multi-select (click, shift-click, ctrl-click)
   - View selection count

2. **Create Batch**
   - Click "Check Selected Profiles"
   - System creates batch
   - Batch appears in Batch tab

### 3.2. Profile Navigation

1. **Pagination**
   - Server-side pagination for efficient data loading
   - Configurable page sizes (25, 50, 100 items per page)
   - Synchronized across views
   - Maintains state during filtering

2. **Filtering**
   - Real-time search
   - Niche filtering
   - Status filtering
   - See [FILTERING.md](client/docs/FILTERING.md) for details

### 3.3. Batch Processing and Queueing

1. **Start Processing**
   - Select batches in Batch tab
   - Click "Start Selected"
   - System begins processing
   - Batches are automatically queued if a batch is already running

2. **Automatic Queue Management**
   - Batches are processed in order
   - When a batch completes, the next batch in queue automatically starts
   - Queue is continuously reordered to maintain efficiency

3. **Monitor Progress**
   - View progress in real-time
   - Track success rates
   - Handle any errors
   - Observe queue position for pending batches

4. **View Results**
   - Check completion status
   - View story detection results
   - Track profile statistics
   - Review batch processing history

### 3.4. Resource Management

1. **Proxy Assignment**
   - Just-in-time proxy selection
   - Rate limit handling
   - Error recovery

2. **Session Management**
   - Session creation/cleanup
   - Cookie handling
   - Error tracking

## 4. Data Management

### 4.1. Profile Data
- Username
- Niche assignment
- Story check history
- Detection statistics

### 4.2. Batch Data
- Associated profiles
- Progress tracking
- Success rates
- Error states

### 4.3. Resource Data
- Proxy health
- Session status
- Rate limit tracking
- Error counts

## 5. Error Handling

### 5.1. Story Check Errors
- Rate limit detection
- Network error recovery
- Invalid profile handling

### 5.2. Resource Errors
- Proxy failures
- Session expiration
- Connection timeouts

### 5.3. System Errors
- Database errors
- API errors
- Resource cleanup

## 6. Best Practices

### 6.1. Batch Processing
- Reasonable batch sizes
- Monitor success rates
- Handle errors gracefully

### 6.2. Resource Usage
- Efficient proxy rotation
- Session reuse when possible
- Proper cleanup

### 6.3. Error Recovery
- Automatic retries
- Resource rotation
- Error logging

## 7. Performance

### 7.1. System Health
- Monitor proxy health
- Track success rates
- Watch error patterns

### 7.2. Resource Optimization
- Efficient proxy usage
- Session management
- Database operations
- Server-side pagination for large datasets

## 8. Security

### 8.1. Data Protection
- Secure credential storage
- Session management
- Error handling

### 8.2. Access Control
- Local deployment
- Resource isolation
- Error boundaries

## Documentation

- [Filtering System](client/docs/FILTERING.md): Details about the centralized filtering system
- [Pagination System](client/docs/PAGINATION.md): Information about server-side pagination
- [Architecture](ARCHITECTURE.md): System architecture and design
- [Implementation Plan](IMPLEMENTATION_PLAN.md): Development roadmap
- [Workflow](WORKFLOW.md): Common usage patterns

## Conclusion

The Instagram Story Checker provides:
1. Efficient profile management
2. Robust batch processing
3. Comprehensive monitoring
4. Resource optimization
5. Error resilience
6. Scalable data handling

Designed for reliability and maintainability in checking Instagram stories at scale.
