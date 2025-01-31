"""Simplified ProxyStateManager for managing proxy and session states."""

from enum import Enum
from typing import List, Optional
from sqlalchemy.orm import Session
from models.proxy_error_log import ProxyErrorLog
from models.proxy import Proxy, ProxyStatus
from models.session import Session

class ProxySessionState(Enum):
    """State enum for proxies and sessions"""
    ACTIVE = "active"      # Proxy or session is ready for use
    DISABLED = "disabled"  # Proxy or session is not usable

class ProxyStateManager:
    """Manages proxy and session states"""

    def __init__(self, db_session: Session, proxy_log_service):
        """Initialize the state manager.
        
        Args:
            db_session: SQLAlchemy database session
            proxy_log_service: Service for logging proxy events
        """
        self.db = db_session
        self.proxy_log = proxy_log_service
        self.max_retries = 3  # Maximum number of retries before disabling

    def get_state(self, proxy_id: str) -> ProxySessionState:
        """Get current state of a proxy.
        
        Args:
            proxy_id: ID of the proxy
            
        Returns:
            Current state of the proxy
        """
        proxy = self.db.query(Proxy).filter_by(id=proxy_id).first()
        if not proxy or proxy.status != ProxyStatus.ACTIVE:
            return ProxySessionState.DISABLED
        return ProxySessionState.ACTIVE

    def get_session_state(self, session_id: str) -> ProxySessionState:
        """Get current state of a session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            Current state of the session
        """
        session = self.db.query(Session).filter_by(id=session_id).first()
        if not session or session.status != Session.STATUS_ACTIVE:
            return ProxySessionState.DISABLED
        return ProxySessionState.ACTIVE

    def transition_proxy_state(self, proxy_id: str, new_state: ProxySessionState, reason: str) -> bool:
        """Attempt to transition a proxy to a new state.
        
        Args:
            proxy_id: ID of the proxy
            new_state: Desired new state
            reason: Reason for the state change
            
        Returns:
            True if transition was successful, False otherwise
        """
        proxy = self.db.query(Proxy).filter_by(id=proxy_id).first()
        if not proxy:
            return False
        
        # Update proxy state
        if new_state == ProxySessionState.ACTIVE:
            proxy.status = ProxyStatus.ACTIVE
        else:
            proxy.status = ProxyStatus.DISABLED
        
        # Create error log entry if transitioning to DISABLED
        if new_state == ProxySessionState.DISABLED:
            error_log = ProxyErrorLog(
                proxy_id=proxy_id,
                error_message=reason,
                state_change=True
            )
            self.db.add(error_log)
        
        self.db.commit()
        self.proxy_log.log_state_change(
            proxy_id=proxy_id,
            new_state=new_state,
            reason=reason
        )
        return True

    def transition_session_state(self, session_id: str, new_state: ProxySessionState, reason: str) -> bool:
        """Attempt to transition a session to a new state.
        
        Args:
            session_id: ID of the session
            new_state: Desired new state
            reason: Reason for the state change
            
        Returns:
            True if transition was successful, False otherwise
        """
        session = self.db.query(Session).filter_by(id=session_id).first()
        if not session:
            return False
        
        # Update session state
        if new_state == ProxySessionState.ACTIVE:
            session.status = Session.STATUS_ACTIVE
        else:
            session.status = Session.STATUS_DISABLED
        
        # Create error log entry if transitioning to DISABLED
        if new_state == ProxySessionState.DISABLED:
            error_log = ProxyErrorLog(
                session_id=session_id,
                error_message=reason,
                state_change=True
            )
            self.db.add(error_log)
        
        self.db.commit()
        self.proxy_log.log_state_change(
            session_id=session_id,
            new_state=new_state,
            reason=reason
        )
        return True

    def get_active_proxies(self) -> List[Proxy]:
        """Get list of active proxies.
        
        Returns:
            List of active proxies
        """
        return self.db.query(Proxy).filter_by(status=ProxyStatus.ACTIVE).all()

    def get_active_sessions(self) -> List[Session]:
        """Get list of active sessions.
        
        Returns:
            List of active sessions
        """
        return self.db.query(Session).filter_by(status=Session.STATUS_ACTIVE).all()

    def handle_request_result(self, proxy_id: str, session_id: str, success: bool,
                            response_time: Optional[float] = None,
                            error: Optional[str] = None) -> None:
        """Handle result of proxy request.
        
        Args:
            proxy_id: ID of the proxy
            session_id: ID of the session
            success: Whether the request was successful
            response_time: Optional response time in seconds
            error: Optional error message
        """
        if not success and error:
            # Get current retry count from error logs
            recent_errors = self.db.query(ProxyErrorLog).filter_by(
                proxy_id=proxy_id,
                session_id=session_id,
                state_change=False
            ).order_by(ProxyErrorLog.timestamp.desc()).limit(self.max_retries).all()

            # Create error log entry
            error_log = ProxyErrorLog(
                proxy_id=proxy_id,
                session_id=session_id,
                error_message=error,
                state_change=len(recent_errors) >= self.max_retries - 1
            )
            self.db.add(error_log)
            self.db.commit()

            # If max retries exceeded, disable proxy and session
            if len(recent_errors) >= self.max_retries - 1:
                self.transition_proxy_state(
                    proxy_id=proxy_id,
                    new_state=ProxySessionState.DISABLED,
                    reason=f"Max retries ({self.max_retries}) exceeded: {error}"
                )
                self.transition_session_state(
                    session_id=session_id,
                    new_state=ProxySessionState.DISABLED,
                    reason=f"Max retries ({self.max_retries}) exceeded: {error}"
                )