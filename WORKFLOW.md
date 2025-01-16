# Single Source of Truth: Workflow & Data Flows

## 1. Data Foundations

### 1.1. Master List

**Structure**:
- Username (primary key)
- Niche
- Status (active/deleted)
- Date Last Checked
- Date Last Detected
- Total Checks
- Total Times Detected

**Role**:
- Central repository for all Instagram profiles
- No duplicates allowed
- Source for all operations (batch checks, results display)

**Potential Conflicts & Mitigations**:
1. **Duplicate Usernames**
   - *Issue*: Username exists during import
   - *Mitigation*: 
     - Skip existing entries
     - Alphabetical sorting for faster search

2. **Concurrent Writes**
   - *Issue*: Multiple processes updating single profile
   - *Mitigation*:
     - Row-level locking
     - One batch per niche limit
     - No profile duplication

### 1.2. Daily Story Targets

**Purpose**:
- Store daily story count goals per niche
- Example: `Fitness: 20 stories/day`

**Usage**:
- Drives batch auto-trigger when below target

**Conflicts & Mitigations**:
- *Issue*: Mid-day target changes
- *Mitigation*: Changes only affect future triggers

## 2. Interface Workflows

### 2.1. Niche Feed Tab

**Components**:
1. **Niche List (Left Panel)**
2. **Profile List (Right Panel)**
3. **File Importer**
4. **Filter & Sort Controls**

**Workflows**:

1. **Niche Management**
   - Create: Add new niche name
   - Edit: Update existing niche
   - Delete: Remove niche (profiles revert to unassigned)
   - Reorder: Visual organization only

2. **Profile Management**
   - View profiles by niche
   - Bulk actions (delete/reassign)
   - Pagination for large datasets

3. **Import Process**
   - Validate usernames from .txt
   - Skip duplicates
   - Ignore malformed entries

### 2.2. Batch + Results Tab

**Batch Control**:

1. **Manual Trigger**
   - User selects niche and profile count
   - System creates batch record
   - Status progression: Pending → In Progress → Completed

2. **Auto Trigger**
   - Hourly random-minute check
   - Triggers if below daily target
   - Rate limiting prevents overlap

**Results Display**:
- 24-hour story detection window
- Niche/time filtering
- Bulk username copy
- Auto-purge after 24 hours

### 2.3. Settings Tab

**Configurations**:
1. **Master List View**
   - Paginated table display
   - Basic CRUD operations

2. **Story Targets**
   - Per-niche daily goals
   - Reasonable limits (~800 max)

3. **Rate Controls**
   - Profiles per minute
   - Thread count (default: 3)

4. **Proxy Management**
   - Add/remove proxies
   - Validation checks
   - Format: `ip:port:user:pass`

## 3. Batch Processing

### 3.1. Creation Flow

1. **Pre-Check**
   - Verify proxy availability
   - Confirm no existing niche batch
   - Validate rate limits

2. **Queue**
   - Generate batch ID
   - Set initial pending status

3. **Processing**
   - Update status to "In Progress"
   - Process profiles (sequential/parallel)
   - Update profile metrics

4. **Completion**
   - Mark batch completed
   - Record statistics

### 3.2. Key Conflict Mitigations

1. **Batch Isolation**
   - One active batch per niche
   - System verification before creation

2. **Rate Protection**
   - Proxy rotation
   - Thread limits
   - Per-minute caps

3. **Data Consistency**
   - Single-batch-per-niche rule
   - Database-level locking where needed

## 4. Example Workflow

1. **Setup**
   - Configure story targets
   - Add proxies
   - Set rate limits

2. **Profile Import**
   - Import usernames
   - Assign to niche
   - Handle duplicates

3. **Batch Processing**
   - Auto/manual trigger
   - Profile checking
   - Results updating

4. **Results Management**
   - Monitor detections
   - Copy usernames
   - Track statistics

## 5. System Features

### 5.1. Logging

**Key Metrics**:
- Batch statistics
- Import results
- Error tracking
- Proxy performance

### 5.2. Security

- Cloud hosting
- HTTPS encryption
- Credential management
- Single-user focus

## 6. Conflict Summary

### Critical Conflicts & Solutions

1. **Data Integrity**
   - Skip duplicate usernames
   - Single batch per niche
   - Row-level locking

2. **Performance**
   - Pagination for large datasets
   - Proxy rotation
   - Rate limiting

3. **User Actions**
   - Batch cancellation handling
   - Safe proxy management
   - Target limit enforcement

4. **System Limits**
   - Thread count restrictions
   - Reasonable story targets
   - Auto-purge implementation

## Conclusion

This workflow ensures:
1. Data consistency through clear rules
2. Conflict prevention via systematic checks
3. Efficient processing with rate protection
4. User-friendly operation with safety guards

The system provides robust, scalable Instagram story monitoring while maintaining data integrity and preventing common operational issues.
