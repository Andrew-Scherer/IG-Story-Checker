# Instagram Story Checker

A tool designed to import, organize, check, and monitor Instagram profiles for active stories. The workflow is centered around a Master List, ensuring centralized data management for usernames, niche assignments, and statuses.

## 1. Overview

This tool provides comprehensive functionality for:
- **Importing** Instagram profiles
- **Organizing** profiles by niche
- **Checking** for active stories
- **Monitoring** story activity in real-time

## 2. Tab 1: Niche Feed

The Niche Feed tab manages Instagram profiles grouped by niche, featuring two main panels and auxiliary features.

### 2.1. Niche List (Left Panel)

**Purpose**: Organize profiles by niche and allow easy category switching.

**Features**:
1. **Scrollable List of Niches**: Displays all available niche categories
2. **Actions**:
   - Add Niche: Create new categories
   - Rename Niche: Edit existing names
   - Delete Niche: Remove categories (profiles remain in master list)
   - Reorder Niches: Change display order

**Master List Integration**: Each niche corresponds to a column value in the master list.

### 2.2. Profile List (Right Panel)

**Purpose**: Display Instagram profiles belonging to the selected niche.

**Columns**:
1. Instagram URL
2. Instagram Username
3. Date Last Checked
4. Date Last Detected
5. Total Number of Story Checks
6. Total Number of Times a Story Was Detected

**Actions**:
- Bulk Mark as Deleted
- Assign to Niche

### 2.3. File Importer

**Purpose**: Import `.txt` files containing Instagram usernames.

**Behavior**:
- Validates against Master List
- Skips existing usernames
- Adds only new entries

### 2.4. Filter and Sort Controls

**Filters**:
- Status (active/deleted)

**Sort Options**:
1. Last Checked
2. Last Detected
3. Total Checks
4. Times Detected

## 3. Tab 2: Batch + Results

Manages batch processing and displays recent story detections.

### 3.1. Batch Controls & Management

#### Batch Control Panel
- **Manual Trigger** ("Run Batch Now" button)
  - Niche selection
  - Number of profiles selection
- **Batch Status Indicators**
  - Pending batches
  - In-progress batches
  - Completed batches

#### Automatic Trigger
Runs hourly at random minutes when:
1. Results show fewer active stories than daily target
2. No other batch for that niche is scheduled/running

#### Batch Details
- Niche assignment
- Profile count
- Progress tracking
- Timestamps
- Proxy/worker usage

### 3.2. Results Display

1. **Story Detections**
   - Shows profiles with active stories (last 24 hours)
2. **Filters**
   - By niche
   - By detection timestamp
3. **Bulk Operations**
   - Select multiple profiles
   - Copy usernames to clipboard
4. **Auto-Purge**
   - 24-hour expiration

## 4. Tab 3: Settings

Global configurations for tool operation.

### 4.1. Master List Management

**View Master List Table**:
1. Username
2. Niche
3. Status
4. Last Updated

### 4.2. Daily Story Targets

- Configure Stories Needed Per Day per niche
- Drives automatic batch triggering

### 4.3. Rate Limiting

Configure:
- Profiles per minute
- Thread count

### 4.4. Proxy Management

- Add/remove proxies
- Format: `ip:port:user:pass`

## 5. Master List Integration

### 5.1. Centralized Data
Single source of truth for all profile data.

### 5.2. Data Fields
- Username
- Niche
- Status
- Date Last Checked
- Date Last Detected
- Total Checks
- Total Times Detected

## 6. Batching

### 6.1. How Batching Works

1. **Batch Creation**
   - Based on niche, status, and check history
2. **Batch Size**
   - Configurable
3. **Batch Execution**
   - Proxy-based
   - Rate-limited
4. **Batch Status**
   - Lifecycle tracking
   - Archival system

### 6.2. Batch Triggers

1. **Automatic**
   - Hourly checks
2. **Manual**
   - User-initiated

### 6.3. Batch Prioritization
- Longest idle profiles first

### 6.4. Retention
- 7-day retention for completed batches
- Automatic archival

### 6.5. Configuration
- Batch sizing
- Rate limits
- Success rate tracking
- Proxy settings

## 7. Example Workflow

1. **Initial Check**
   - Niche: Fitness
   - Target: 20 stories
   - Current: 10 stories
   - Shortfall: 10 stories
   - Success rate: 15%
   - Batch size: 100 profiles

2. **Processing**
   - Sequential/parallel checking
   - Real-time results

3. **Post-Processing**
   - Results display
   - Master list updates

4. **Next Batch**
   - Automatic/manual triggering

## 8. Deployment & Access Control

### Cloud Hosting
- Scalable cloud deployment
- Remote accessibility

### Security
- Username/password authentication
- Role-based access (optional)
- HTTPS encryption
- Strong password requirements
- Optional 2FA

## Conclusion

The tool provides three main interfaces:
1. **Niche Feed**: Profile management
2. **Batch + Results**: Processing and monitoring
3. **Settings**: System configuration

Designed for scalability, security, and user-friendly operation in near real-time Instagram story monitoring.
