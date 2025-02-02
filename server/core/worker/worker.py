"""
Worker Implementation
Handles story checking with state management
"""

from datetime import datetime, UTC
from typing import Optional, Tuple
from models.batch import BatchProfile
from models.proxy import Proxy
from models.session import Session
from core.story_checker import StoryChecker
from core.proxy_session import ProxySession
from .worker_state import WorkerState
from flask import current_app
from models.proxy_error_log import ProxyErrorLog
from extensions import db

class Worker:
    """Worker that performs story checks with state management"""

    def __init__(self, proxy: Proxy, session: Session):
        """Initialize worker

        Args:
            proxy: Proxy model instance
            session: Session model instance
        """
        self.proxy_session = ProxySession(proxy, session)
        self.story_checker = StoryChecker(self.proxy_session)
        self.state = WorkerState()
        self.current_profile = None
        self.last_check: Optional[datetime] = None  # Time of the last check
        current_app.logger.debug(f'Initialized Worker with proxy {self.proxy_session.proxy_url_safe}')

    @property
    def is_disabled(self) -> bool:
        return self.state.is_disabled

    @property
    def is_rate_limited(self) -> bool:
        return self.state.is_rate_limited

    def check_story(self, batch_profile: BatchProfile) -> Tuple[bool, bool]:
        """Check story for a profile

        Args:
            batch_profile: BatchProfile to check

        Returns:
            Tuple of (success, has_story)
            - success: True if check succeeded, False if failed
            - has_story: True if story found, False if no story (only valid if success is True)
        """
        username = batch_profile.profile.username
        current_app.logger.debug(f'Starting check_story for profile {username} using proxy {self.proxy_session.proxy_url_safe}')
        
        if not self._pre_check_validations(batch_profile):
            return False, False

        self._enforce_minimum_interval()

        self.current_profile = batch_profile
        self.last_check = datetime.now(UTC)
        current_app.logger.info(f'Beginning story check for {username} via proxy {self.proxy_session.proxy_url_safe}')

        try:
            if self.state.check_rate_limit():
                error_msg = f'Worker with proxy {self.proxy_session.proxy_url_safe} hit rate limit'
                current_app.logger.warning(error_msg)
                batch_profile.error = error_msg
                return False, False

            current_app.logger.info(f'Initiating story check via story_checker for {username}')
            has_story = self.story_checker.check_story(username)
            current_app.logger.info(f'Story check completed for {username}: has_story={has_story}')

            self._process_success_result(batch_profile, has_story)
            return True, has_story

        except Exception as e:
            return self._handle_error(batch_profile, e)

        finally:
            self._cleanup(batch_profile)

    def _pre_check_validations(self, batch_profile: BatchProfile) -> bool:
        """Perform pre-check validations"""
        if self.is_disabled:
            error_msg = f'Worker with proxy {self.proxy_session.proxy_url_safe} is disabled'
            current_app.logger.warning(error_msg)
            batch_profile.error = error_msg
            return False

        if self.is_rate_limited:
            error_msg = f'Worker with proxy {self.proxy_session.proxy_url_safe} is rate limited'
            current_app.logger.warning(error_msg)
            batch_profile.error = error_msg
            return False

        return True

    def _enforce_minimum_interval(self):
        """Enforce minimum interval between checks"""
        if self.last_check is not None:
            elapsed = (datetime.now(UTC) - self.last_check).total_seconds()
            if elapsed < 20:
                wait_time = 20 - elapsed
                current_app.logger.info(f'Waiting {wait_time} seconds to respect rate limit')
                # Sleep since we're in a synchronous context
                import time
                time.sleep(wait_time)

    def _process_success_result(self, batch_profile: BatchProfile, has_story: bool):
        """Process successful story check result"""
        end_time = datetime.now(UTC)
        batch_profile.status = 'completed'
        batch_profile.has_story = has_story
        batch_profile.processed_at = end_time
        batch_profile.proxy_id = self.proxy_session.proxy.id
        batch_profile.error = None  # Clear any previous error

        # Calculate response time in milliseconds
        response_time = int((end_time - self.last_check).total_seconds() * 1000)
        self.response_time = response_time
        self.proxy_session.proxy.record_request(success=True, response_time=response_time)

        profile = batch_profile.profile
        profile.total_checks += 1
        if has_story:
            profile.total_detections += 1
            profile.active_story = True
            profile.last_story_detected = end_time
        else:
            profile.active_story = False

        self.state.record_success()
        current_app.logger.info(f'Successfully completed story check for {profile.username} (has_story={has_story})')

    def _handle_error(self, batch_profile: BatchProfile, e: Exception) -> Tuple[bool, bool]:
        """Handle errors during story check"""
        # Sanitize error message
        error_text = str(e).replace('\x00', '')
        error_msg = f'Error checking story for {batch_profile.profile.username} via proxy {self.proxy_session.proxy_url_safe}: {type(e).__name__} - {error_text}'
        current_app.logger.error(error_msg, exc_info=True)

        is_rate_limit = "Rate limited" in error_text
        self.state.record_error(is_rate_limit)

        # Record error in proxy
        self.proxy_session.proxy.record_request(success=False, error_msg=error_text)

        # Create and save ProxyErrorLog entry
        error_log = ProxyErrorLog(
            proxy_id=self.proxy_session.proxy.id,
            session_id=self.proxy_session.session.id,
            error_message=error_msg[:500],  # Truncate if necessary
            state_change=is_rate_limit,
            transition_reason='Rate limit detected' if is_rate_limit else 'Error occurred',
        )
        db.session.add(error_log)
        db.session.commit()

        batch_profile.status = 'failed'
        batch_profile.error = error_msg[:500]  # Truncate to fit database field

        if is_rate_limit:
            current_app.logger.warning(f'Rate limit detected for {batch_profile.profile.username}, allowing retry')
            self.state.is_rate_limited = True
        else:
            current_app.logger.error(f'Non-rate-limit error for {batch_profile.profile.username}, marking as failed')

        return False, False

    def _cleanup(self, batch_profile: BatchProfile):
        """Perform cleanup after story check"""
        self.current_profile = None
        self.story_checker.cleanup()
        current_app.logger.debug(f'Worker cleanup completed for {batch_profile.profile.username}')

    def is_available(self) -> bool:
        """Check if the worker is available for new tasks"""
        return not self.is_disabled and not self.is_rate_limited

    def clear_rate_limit(self):
        """Clear rate limit status"""
        self.state.clear_rate_limit()
        current_app.logger.debug(f'Cleared rate limit for worker with proxy {self.proxy_session.proxy_url_safe}')
