# Application Architecture

## System Overview

```
┌─────────────────────────────────────────┐
│              Client Layer               │
│  ┌─────────────────┐  ┌───────────────┐│
│  │    React UI     │  │Zustand Stores ││
│  └─────────────────┘  └───────────────┘│
└───────────────────────┬─────────────────┘
                        │
┌───────────────────────▼─────────────────┐
│              Server Layer               │
│  ┌─────────────┐  ┌──────────────────┐ │
│  │  Flask API  │  │  Worker Manager  │ │
│  └─────────────┘  └──────────────────┘ │
└───────────────────────┬─────────────────┘
                        │
┌───────────────────────▼─────────────────┐
│              Data Layer                 │
│  ┌─────────────┐  ┌──────────────────┐ │
│  │ PostgreSQL  │  │   Story Results  │ │
│  └─────────────┘  └──────────────────┘ │
└─────────────────────────────────────────┘
```

## Directory Structure

```
instagram-story-checker/
├── client/                      # Frontend React application
│   ├── src/
│   │   ├── components/         # Reusable UI components
│   │   │   ├── common/        # Shared components (Table, Button, etc.)
│   │   │   ├── niche/         # Niche feed and profile management
│   │   │   ├── batch/         # Batch table and controls
│   │   │   └── settings/      # Proxy and system settings
│   │   ├── stores/            # Zustand state management
│   │   ├── api/               # API client
│   │   └── styles/            # Global styles and variables
│   └── tests/                 # Frontend tests
│
├── server/                     # Backend Flask application
│   ├── api/                   # API endpoints
│   │   ├── niche.py          # Niche management
│   │   ├── profile.py        # Profile management
│   │   ├── batch.py          # Batch operations
│   │   └── proxy.py          # Proxy management
│   ├── core/                  # Core functionality
│   │   ├── worker_manager.py # Worker pool management
│   │   ├── story_checker.py  # Story checking logic
│   │   └── batch_processor.py # Batch processing
│   ├── models/               # Database models
│   │   ├── base.py          # Base model
│   │   ├── profile.py       # Profile schema
│   │   ├── niche.py         # Niche schema
│   │   ├── batch.py         # Batch schema
│   │   ├── proxy.py         # Proxy schema
│   │   └── session.py       # Session schema
│   └── tests/               # Backend tests
```

## Component Responsibilities

### Frontend Components

#### 1. Common Components (`client/src/components/common/`)
- `Table.jsx`: Multi-select data table with sorting
- `Button.jsx`: Action buttons with loading states
- `Input.jsx`: Form inputs with validation
- `Modal.jsx`: Confirmation dialogs
- `Spinner.jsx`: Loading indicators

#### 2. Niche Feed (`client/src/components/niche/`)
- `NicheFeed.jsx`: Main niche management view
- `ProfileList.jsx`: Profile selection and management
- `FileImporter.jsx`: Profile import from files

#### 3. Batch Management (`client/src/components/batch/`)
- `BatchTable.jsx`: Batch listing and controls
  - Multi-select functionality
  - Progress tracking
  - Status display
  - Action buttons (start/stop/delete)

#### 4. Settings (`client/src/components/settings/`)
- `ProxyManager.jsx`: Proxy configuration
- `Settings.jsx`: System settings

### Backend Components

#### 1. API Layer (`server/api/`)
- `niche.py`: Niche CRUD operations
- `profile.py`: Profile management
- `batch.py`: Batch operations
  - Creation from selected profiles
  - Status management
  - Progress tracking
  - Deletion with cleanup
- `proxy.py`: Proxy configuration

#### 2. Core Processing (`server/core/`)
- `worker_manager.py`: Worker pool management
  - Proxy assignment
  - Session handling
  - Rate limiting
- `story_checker.py`: Story detection
- `batch_processor.py`: Batch execution

#### 3. Data Models (`server/models/`)
- `batch.py`: Batch and batch profile tracking
- `profile.py`: Profile data and stats
- `niche.py`: Niche organization
- `proxy.py`: Proxy configuration
- `session.py`: Session management

## State Management

### Zustand Stores

1. **Batch Store** (`batchStore.js`)
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

2. **Profile Store** (`profileStore.js`)
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

3. **Niche Store** (`nicheStore.js`)
```javascript
{
  niches: [],
  selectedNiche: null,
  loading: false,
  error: null,
  actions: {
    fetchNiches,
    createNiche,
    deleteNiche
  }
}
```

4. **Proxy Store** (`proxyStore.js`)
```javascript
{
  proxies: [],                    // List of available proxies
  loading: false,                 // Loading state
  error: null,                    // Error state
  healthHistory: {},             // Historical health data per proxy
  rotationEnabled: false,        // Auto rotation status
  rotationInterval: 60,          // Minutes between rotations
  actions: {
    fetchProxies,               // Get all proxies
    addProxy,                   // Add new proxy with session
    removeProxy,                // Remove proxy and cleanup
    testProxy,                  // Test proxy connectivity
    updateHealth,               // Update proxy health metrics
    toggleRotation,             // Enable/disable auto rotation
    setRotationInterval,        // Update rotation timing
    getHealthyProxies,         // Get proxies meeting health criteria
    getDegradedProxies,        // Get proxies needing attention
    getAvailableProxies        // Get proxies ready for assignment
  }
}
```

## Data Flows

### 1. Profile Selection Flow
```
ProfileList → Profile Store → BatchTable → Batch Store → API
```

### 2. Batch Processing Flow
```
BatchTable → Batch Store → API → Worker Manager → 
Story Checker → Database → API → Batch Store → UI
```

### 3. Proxy Management Flow
```
ProxyManager → Proxy Store → API → Worker Manager → Database → API → Proxy Store → UI

Proxy Health Flow:
1. Worker makes request through proxy
2. Worker reports metrics to Worker Manager
3. Worker Manager updates proxy health
4. Health metrics propagate to UI
5. Auto-rotation triggers if needed

Session Management Flow:
1. Proxy created with Instagram session
2. Session assigned to worker
3. Worker validates session
4. Session status updated
5. Failed sessions trigger proxy rotation
```

## Testing Strategy

### Frontend Testing
- Component rendering and interaction
- Store state management
- API integration
- Error handling

### Backend Testing
- API endpoints
- Worker management
- Batch processing
- Database operations

## Security

1. **API Security**
- Input validation
- Error handling
- Rate limiting

2. **Resource Management**
- Proxy Management
  - Automatic proxy rotation based on health metrics
  - Session validation and cleanup
  - Error threshold monitoring
  - Request rate limiting
  - Performance tracking
  - Health history maintenance
  - Load balancing across proxy pool
- Session Management
  - Session cookie validation
  - Session-proxy pairing
  - Failed session detection
  - Automatic session rotation
  - Session cleanup on proxy removal
- Error Recovery
  - Automatic retry with backoff
  - Circuit breaking for failed proxies
  - Session regeneration
  - Worker reassignment

## Deployment

```
┌─────────────┐    ┌─────────────┐
│ React Build │────│ Flask API   │
└─────────────┘    └──────┬──────┘
                          │
                   ┌──────▼──────┐
                   │ PostgreSQL  │
                   └─────────────┘
```

This architecture provides:
1. Clear component separation
2. Efficient state management
3. Robust error handling
4. Scalable processing
5. Comprehensive testing
