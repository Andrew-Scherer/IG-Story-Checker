# ProxyManager Refactor Plan

This document outlines a phased plan to refactor the `ProxyManager` in the IG Story Checker application. The goal is to fragment the responsibilities of the `ProxyManager` into multiple modules before integrating the functionalities of both `ProxyManager` classes into a single source of truth.

---

## Overview

Currently, there are two `ProxyManager` implementations:

1. **`server/core/proxy_manager.py`**
   - Manages proxies at the application level.
   - Handles overall proxy health monitoring, rotation strategies, and interacts with the database.

2. **`server/core/worker/proxy_manager.py`**
   - Manages proxies within the worker processes.
   - Handles proxy-session pairs, proxy states, and metrics within the worker context.

---

## Phase 1: Analyze Current Implementations

### Tasks

- [ ] **Review `server/core/proxy_manager.py`**:
  - Understand its responsibilities and functionalities.
  - Document core methods and attributes.
  
- [ ] **Review `server/core/worker/proxy_manager.py`**:
  - Understand its responsibilities and functionalities.
  - Document core methods and attributes.

- [ ] **Identify Overlaps and Differences**:
  - Compare both implementations to find overlapping functionalities.
  - Note any differences in method signatures and data handling.

### Potential Conflicts

- Differences in method implementations and data structures.
- Inconsistent state management between application and worker contexts.
- Conflicts arising from merging differing approaches to proxy management.

---

## Phase 2: Fragment Responsibilities into Modules

### Tasks

- [ ] **Identify Core Responsibilities to Separate**:
  - Proxy Retrieval and Rotation
  - Health Monitoring
  - Session Management
  - Metrics Collection

- [ ] **Create New Modules for Each Responsibility**:
  - `proxy_retriever.py`
  - `health_monitor.py`
  - `session_manager.py`
  - `metrics_collector.py`

- [ ] **Move Relevant Code into Modules**:
  - Extract methods and attributes from both `ProxyManager` files.
  - Ensure each module has a single, clear responsibility.

- [ ] **Define Clear Interfaces**:
  - Establish clear method signatures for interaction between modules.
  - Use abstraction where necessary to maintain loose coupling.

### Potential Conflicts

- Dependencies between modules leading to circular imports.
- Ensuring that shared data is accessible where needed without violating encapsulation.
- Adjusting existing code to use new module structures.

---

## Phase 3: Merge Functionalities

### Tasks

- [ ] **Unify Proxy Management Logic**:
  - Consolidate overlapping methods from both implementations.
  - Ensure consistent proxy rotation strategies (e.g., round-robin).

- [ ] **Standardize State Management**:
  - Create a unified approach for tracking proxy states (active, disabled, rate-limited).
  - Ensure thread safety where necessary.

- [ ] **Update Data Models if Needed**:
  - Modify database models to support unified proxy management (if required).
  - Migrate any discrepancy in data handling.

### Potential Conflicts

- Incompatibility between worker and application processes due to different expectations.
- Changes to data models affecting other parts of the application.
- Need for synchronization mechanisms to handle concurrent access in workers.

---

## Phase 4: Update Codebase and Resolve Conflicts

### Tasks

- [ ] **Refactor Codebase to Use New Modules**:
  - Replace references to old `ProxyManager` instances with new module functions or classes.
  - Ensure imports are updated throughout the codebase.

- [ ] **Remove Deprecated Code**:
  - Delete the old `proxy_manager.py` files after ensuring all functionalities are covered.
  - Clean up any residual references.

- [ ] **Address Conflicts and Issues**:
  - Debug any issues arising from the refactor.
  - Resolve any dependency conflicts or unexpected behavior.

### Potential Conflicts

- Risk of breaking existing functionality if the refactor isn't thorough.
- Possible performance impacts due to changes in proxy management.
- Ensuring backward compatibility with existing data and configurations.

---

## Phase 5: Testing and Validation

### Tasks

- [ ] **Write Unit Tests for Each Module**:
  - Ensure all new modules are adequately tested.
  - Cover edge cases and potential failure points.

- [ ] **Perform Integration Testing**:
  - Test interactions between modules.
  - Validate that proxy rotation and session management work as expected.

- [ ] **Conduct Load Testing**:
  - Assess performance under expected workloads.
  - Identify any bottlenecks or resource contention issues.

### Potential Conflicts

- Uncovered bugs due to changes in proxy management logic.
- Latent issues in concurrency when handling multiple worker processes.
- Ensuring test environments accurately reflect production settings.

---

## Phase 6: Documentation and Deployment

### Tasks

- [ ] **Update Documentation**:
  - Document new module structures and their responsibilities.
  - Provide usage guidelines and examples.

- [ ] **Train Team Members on Changes**:
  - Share the refactored design with the team.
  - Conduct code reviews to familiarize others with the new structure.

- [ ] **Prepare for Deployment**:
  - Ensure all changes are merged and conflicts resolved.
  - Plan deployment to minimize disruptions.

### Potential Conflicts

- Team members may need time to adjust to the new code structure.
- Possible oversights in documentation leading to confusion.
- Coordination required to deploy changes without impacting active processes.

---

## Conclusion

Fragmenting the `ProxyManager` responsibilities before refactoring allows for a cleaner, more maintainable codebase. By carefully planning each phase and anticipating potential conflicts, we can ensure a smooth transition to a unified and efficient proxy management system.
