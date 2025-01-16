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
│  │  Flask API  │  │  Batch Processor │ │
│  └─────────────┘  └──────────────────┘ │
└───────────────────────┬─────────────────┘
                        │
┌───────────────────────▼─────────────────┐
│              Data Layer                 │
│  ┌─────────────┐  ┌──────────────────┐ │
│  │ PostgreSQL  │  │   Redis Cache    │ │
│  └─────────────┘  └──────────────────┘ │
└─────────────────────────────────────────┘
```

## Directory Structure

```
instagram-story-checker/
├── client/                      # Frontend React application
│   ├── src/
│   │   ├── components/         # Reusable UI components
│   │   │   ├── common/        # Shared components
│   │   │   ├── niche/         # Niche-related components
│   │   │   ├── batch/         # Batch-related components
│   │   │   └── settings/      # Settings components
│   │   ├── stores/            # Zustand state management
│   │   ├── api/               # API integration
│   │   └── utils/             # Helper functions
│   └── tests/                 # Frontend test suites
│       ├── components/        # Component tests
│       ├── stores/           # Store tests
│       └── api/              # API integration tests
│
├── server/                      # Backend Flask application
│   ├── api/                    # API endpoints
│   │   ├── niche.py           # Niche management
│   │   ├── profile.py         # Profile management
│   │   ├── batch.py           # Batch operations
│   │   └── settings.py        # Settings & session management
│   ├── core/                   # Core functionality
│   │   ├── batch_processor.py # Batch processing logic
│   │   ├── story_checker.py   # Instagram story checking
│   │   ├── session_manager.py # Instagram session management
│   │   └── scheduler.py       # Task scheduling
│   ├── models/                 # Database models
│   │   ├── base.py           # Base model configuration
│   │   ├── profile.py        # Profile schema
│   │   ├── niche.py          # Niche schema
│   │   ├── batch.py          # Batch schema
│   │   ├── story.py          # Story schema
│   │   ├── session.py        # Session schema
│   │   └── settings.py       # Settings schema
│   ├── migrations/            # Database migrations
│   └── tests/                 # Backend test suites
│       ├── api/              # API endpoint tests
│       ├── core/             # Core logic tests
│       ├── models/           # Model tests
│       └── integration/      # Integration tests
```

## Component Responsibilities

### Frontend Components

#### 1. Common Components (`client/src/components/common/`)
- `Button.jsx`: Reusable button component with consistent styling
- `Input.jsx`: Form input component with validation support
- `Table.jsx`: Data table with sorting and filtering
- `Modal.jsx`: Popup dialog component for forms and confirmations

#### 2. Niche Management (`client/src/components/niche/`)
- `NicheList.jsx`: Manages niche categories and organization
- `ProfileList.jsx`: Displays and manages profiles within niches
- `FileImporter.jsx`: Handles bulk username imports from files
- `FilterControls.jsx`: Profile filtering and sorting controls

#### 3. Batch Operations (`client/src/components/batch/`)
- `BatchControl.jsx`: Controls batch execution and scheduling
- `ResultsDisplay.jsx`: Displays batch results with filtering and actions
- `BatchProgress.jsx`: Real-time progress tracking

#### 4. Settings Management (`client/src/components/settings/`)
- `MasterList.jsx`: Central profile database management
- `StoryTargets.jsx`: Story checking frequency configuration
- `ProxyManager.jsx`: Proxy and session configuration with monitoring

### Backend Components

#### 1. API Layer (`server/api/`)
- `niche.py`: CRUD operations for niche management
- `profile.py`: Profile creation, updates, and queries
- `batch.py`: Batch creation and control endpoints
- `settings.py`: System configuration and session management

#### 2. Core Processing (`server/core/`)
- `batch_processor.py`: Manages batch execution and threading
- `story_checker.py`: Instagram story detection using API
- `proxy_manager.py`: Proxy and session management
- `scheduler.py`: Automated task scheduling and execution

#### 3. Data Models (`server/models/`)
- `base.py`: SQLAlchemy base configuration and mixins
- `profile.py`: Instagram profile data and status
- `niche.py`: Niche categories and relationships
- `batch.py`: Batch execution tracking
- `story.py`: Story detection results and history
- `proxy.py`: Proxy configuration and session data
- `settings.py`: Application configuration storage

## State Management

### Zustand Stores (`client/src/stores/`)

1. **Proxy Store** (`proxyStore.js`)
```javascript
{
  proxies: {
    active: [],      // Working proxy-session pairs
    cooldown: [],    // Rate-limited pairs
    disabled: []     // Invalid/expired pairs
  },
  stats: {
    checksPerProxy: {},
    successRates: {},
    rateLimits: {}
  },
  actions: {
    addProxy,
    removeProxy,
    updateProxyStatus,
    updateSessionCookie,
    recordStats
  }
}
```

2. **Niche Store** (`nicheStore.js`)
```javascript
{
  niches: [],
  selectedNiche: null,
  actions: {
    addNiche,
    updateNiche,
    deleteNiche,
    reorderNiches
  }
}
```

3. **Profile Store** (`profileStore.js`)
```javascript
{
  profiles: [],
  filters: { status, sortBy },
  actions: {
    importProfiles,
    updateProfile,
    deleteProfiles,
    assignToNiche
  }
}
```

4. **Batch Store** (`batchStore.js`)
```javascript
{
  activeBatches: [],
  results: [],
  actions: {
    createBatch,
    cancelBatch,
    updateBatchStatus,
    clearResults
  }
}
```

5. **Settings Store** (`settingsStore.js`)
```javascript
{
  settings: {
    storyTargets: {},
    proxyConfig: {},
    rateLimit: {},
    sessionConfig: {
      maxChecksPerHour: 200,
      cooldownMinutes: 15,
      minSuccessRate: 0.8
    }
  },
  actions: {
    updateSettings,
    updateProxyConfig,
    updateRateLimit,
    updateSessionConfig
  }
}
```

## Testing Strategy

### 1. Frontend Testing
- **Component Tests** (`client/tests/components/`)
  - Common component behavior
  - User interaction flows
  - State updates
- **Store Tests** (`client/tests/stores/`)
  - State management
  - Action handlers
  - Store interactions
- **API Tests** (`client/tests/api/`)
  - API integration
  - Error handling
  - Response parsing

### 2. Backend Testing
- **API Tests** (`server/tests/api/`)
  - Endpoint functionality
  - Request validation
  - Response formatting
- **Core Tests** (`server/tests/core/`)
  - Batch processing logic
  - Story checking accuracy
  - Session management
  - Scheduler reliability
- **Model Tests** (`server/tests/models/`)
  - Schema validation
  - Relationship integrity
  - Query performance
- **Integration Tests** (`server/tests/integration/`)
  - End-to-end workflows
  - System interactions
  - Performance metrics

## Data Flow

1. **Profile Import Flow**
```
FileImporter → API → Master List → Profile Store → UI Update
```

2. **Batch Processing Flow**
```
BatchControl → API → Batch Processor → Session Manager → Story Checker → 
Results Update → Profile Store → UI Update
```

3. **Settings Update Flow**
```
Settings Component → API → Config Update → 
System Reconfiguration → Status Update
```

4. **Proxy-Session Management Flow**
```
ProxyManager → API → Proxy-Session Validation → 
Health Monitoring → Status Update
```

## Key Integration Points

### 1. Frontend-Backend Integration
- RESTful API endpoints
- WebSocket for real-time updates
- JWT authentication

### 2. Database Integration
- SQLAlchemy ORM
- Migration management
- Connection pooling

### 3. External Service Integration
- Instagram API interaction
- Proxy-session management
- Error handling/retry logic

## Security Measures

1. **Authentication**
- JWT token validation
- Role-based access
- Session management

2. **Data Protection**
- HTTPS encryption
- Input validation
- SQL injection prevention
- Secure session storage

3. **Rate Limiting**
- API request throttling
- Proxy-session pair rotation
- Instagram rate compliance

## Deployment Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │────│  React Frontend │
└────────┬────────┘    └─────────────────┘
         │
┌────────▼────────┐    ┌─────────────────┐
│   Flask API     │────│  Redis Cache    │
└────────┬────────┘    └─────────────────┘
         │
┌────────▼────────┐    ┌─────────────────┐
│   PostgreSQL    │────│  Backup DB      │
└─────────────────┘    └─────────────────┘
```

This architecture ensures:
1. Scalable component structure
2. Clear separation of concerns
3. Maintainable codebase
4. Efficient data flow
5. Robust error handling
6. Comprehensive testing coverage
7. Secure session management
