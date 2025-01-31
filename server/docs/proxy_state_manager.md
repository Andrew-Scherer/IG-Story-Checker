# Proxy State Manager

The ProxyStateManager component is responsible for managing the state transitions of proxies and sessions between ACTIVE and DISABLED states. It implements a simplified retry mechanism with error logging.

## Core Features

1. **Retry Logic**:
   - Maximum of 3 retries for failed requests
   - After 3 consecutive failures, marks the proxy/session as disabled
   - Error logging for each failure with proper context

2. **State Management**:
   - Independent state tracking for proxies and sessions
   - Atomic state transitions with database transactions
   - Error logging with detailed failure reasons

3. **Error Logging**:
   - Integration with ProxyErrorLog model
   - Tracks error history with proper relationships
   - Links errors to both proxies and sessions when applicable

## ProxyStateManager Class

```python
class ProxyStateManager:
    def __init__(self, db_session: Session, proxy_log_service):
        self.db = db_session
        self.proxy_log = proxy_log_service
        self.max_retries = 3  # Maximum number of retries before disabling

    def get_state(self, proxy_id: str) -> ProxySessionState:
        """Get current state of a proxy."""
        # Returns ACTIVE or DISABLED based on proxy status

    def get_session_state(self, session_id: str) -> ProxySessionState:
        """Get current state of a session."""
        # Returns ACTIVE or DISABLED based on session status

    def transition_proxy_state(self, proxy_id: str, new_state: ProxySessionState, reason: str) -> bool:
        """
        Transition a proxy to a new state.
        - Updates proxy status
        - Creates error log entry if disabling
        - Returns success/failure of transition
        """

    def transition_session_state(self, session_id: str, new_state: ProxySessionState, reason: str) -> bool:
        """
        Transition a session to a new state.
        - Updates session status
        - Creates error log entry if disabling
        - Returns success/failure of transition
        """

    def handle_request_result(self, proxy_id: str, session_id: str, success: bool,
                            response_time: Optional[float] = None,
                            error: Optional[str] = None) -> None:
        """
        Handle the result of a proxy request.
        - Logs errors to ProxyErrorLog
        - Tracks consecutive failures
        - Disables proxy/session after max retries
        - Records error details and timestamps
        """
```

## Database Models

The system uses three main models for state management:

1. **Proxy**: Stores proxy information and status
2. **Session**: Stores session information and status
3. **ProxyErrorLog**: Tracks errors with relationships to both proxies and sessions

## Error Handling Flow

1. When a request fails:
   - Create error log entry
   - Check recent error history
   - If 3 consecutive failures:
     - Disable proxy and session
     - Log state change with reason
     - Create final error log entry

## Benefits

- Simpler, more maintainable code
- Clear retry logic
- Better error tracking
- Proper database relationships
- Atomic state changes
- Comprehensive error history