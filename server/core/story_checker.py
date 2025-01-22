"""
Story Checker
Manages HTTP-based Instagram story checking
"""

import aiohttp
import json
import time
from typing import Optional
from datetime import datetime, timezone
from aiohttp_socks import ProxyConnector
from .proxy_session import ProxySession
from flask import current_app

class StoryChecker:
    """Simple HTTP-based story checker"""

    def __init__(self, proxy_session: ProxySession):
        """Initialize checker with proxy session

        Args:
            proxy_session: ProxySession instance with proxy and session info
        """
        self.proxy_session = proxy_session
        self.session: Optional[aiohttp.ClientSession] = None

        # Headers to mimic a real browser with session
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Cookie': f'sessionid={self.proxy_session.session.session}',
            'X-IG-App-ID': '936619743392459'
        }
        current_app.logger.debug(f'Initialized StoryChecker with proxy {self.proxy_session.proxy_url_safe}')

    async def initialize(self) -> None:
        """Initialize HTTP session"""
        if not self.session:
            current_app.logger.debug(f'Creating new aiohttp session with proxy {self.proxy_session.proxy_url_safe}')
            connector = ProxyConnector.from_url(self.proxy_session.proxy_url)
            self.session = aiohttp.ClientSession(
                headers=self.headers,
                connector=connector
            )

    async def check_story(self, username: str) -> bool:
        """Check if profile has an active story using Instagram API

        Args:
            username: Instagram username to check

        Returns:
            True if an active story is found, False otherwise

        Raises:
            Exception: If check fails or rate limited
        """
        start_time = time.time()
        if not self.session:
            current_app.logger.info(f'Initializing new session for {username} check with proxy {self.proxy_session.proxy_url_safe}')
            await self.initialize()

        current_app.logger.info(f'Starting story check for {username} using proxy {self.proxy_session.proxy_url_safe}')

        try:
            # Step 1: Get user ID from profile
            profile_url = f'https://www.instagram.com/api/v1/users/web_profile_info/?username={username}'
            current_app.logger.info(f'Fetching profile info for {username} at {profile_url}')

            profile_start_time = time.time()
            profile_success, user_id = await self._get_profile(profile_url, username)
            profile_duration = time.time() - profile_start_time
            current_app.logger.info(f'Profile fetch for {username} took {profile_duration:.2f} seconds')

            if not profile_success:
                return False

            # Step 2: Get stories data
            stories_url = f'https://www.instagram.com/api/v1/feed/reels_media/?reel_ids={user_id}'
            current_app.logger.info(f'Fetching stories for {username} (ID: {user_id}) at {stories_url}')

            stories_start_time = time.time()
            stories_success, has_story = await self._get_stories(stories_url, username, user_id)
            stories_duration = time.time() - stories_start_time
            current_app.logger.info(f'Stories fetch for {username} took {stories_duration:.2f} seconds')

            if not stories_success:
                return False

            # Record success after both requests complete successfully
            self.proxy_session.record_success()
            total_duration = time.time() - start_time
            current_app.logger.info(f'Total story check for {username} took {total_duration:.2f} seconds')
            return has_story

        except Exception as e:
            error_msg = f'Exception during story check for {username}: {type(e).__name__} - {str(e)}'
            current_app.logger.exception(error_msg)
            self.proxy_session.record_failure()
            raise Exception(error_msg) from e

    async def _get_profile(self, url: str, username: str) -> tuple[bool, Optional[str]]:
        """Get user profile information"""
        request_start_time = time.time()
        async with self.session.get(url) as response:
            response_status = response.status
            current_app.logger.info(f'Profile request status for {username}: {response_status}')
            
            if not self._validate_response(response_status, 'profile', username):
                return False, None

            try:
                data = await response.json()
            except Exception as e:
                error_msg = f'Failed to parse profile JSON for {username}: {str(e)}'
                current_app.logger.error(error_msg)
                self.proxy_session.record_failure()
                return False, None

            current_app.logger.debug(f'Profile response data structure: {list(data.keys()) if data else "empty"}')

            if not self._validate_profile_data(data, username):
                return False, None

            user = data['data']['user']
            user_id = user.get('id')
            if not user_id:
                error_msg = f'No user ID found for {username}'
                current_app.logger.error(error_msg)
                self.proxy_session.record_failure()
                return False, None

            current_app.logger.info(f'Successfully retrieved user ID {user_id} for {username}')
            request_duration = time.time() - request_start_time
            current_app.logger.info(f'Profile request for {username} took {request_duration:.2f} seconds')
            return True, user_id

    async def _get_stories(self, url: str, username: str, user_id: str) -> tuple[bool, bool]:
        """Get user stories information"""
        request_start_time = time.time()
        async with self.session.get(url) as stories_response:
            stories_status = stories_response.status
            current_app.logger.info(f'Stories request status for {username}: {stories_status}')
            
            if not self._validate_response(stories_status, 'stories', username):
                return False, False

            try:
                stories_data = await stories_response.json()
            except Exception as e:
                error_msg = f'Failed to parse stories JSON for {username}: {str(e)}'
                current_app.logger.error(error_msg)
                self.proxy_session.record_failure()
                return False, False

            current_app.logger.debug(f'Stories response data structure: {list(stories_data.keys()) if stories_data else "empty"}')

            if not self._validate_stories_data(stories_data, username, user_id):
                return False, False

            reels = stories_data.get('reels', {})
            user_reel = reels.get(user_id, {})
            story_items = user_reel.get('items', [])
            has_story = bool(story_items)

            if has_story:
                story_count = len(story_items)
                current_app.logger.info(f'Found {story_count} active stories for {username}')
            else:
                current_app.logger.info(f'No active stories found for {username}')

            request_duration = time.time() - request_start_time
            current_app.logger.info(f'Stories request for {username} took {request_duration:.2f} seconds')
            return True, has_story

    def _validate_response(self, status: int, request_type: str, username: str) -> bool:
        """Validate HTTP response status"""
        if status == 429:
            error_msg = f'Rate limited on {request_type} request for {username}'
            current_app.logger.warning(error_msg)
            self.proxy_session.record_failure()
            return False
        elif status != 200:
            error_msg = f'{request_type.capitalize()} request failed for {username} with status {status}'
            current_app.logger.error(error_msg)
            self.proxy_session.record_failure()
            return False
        return True

    def _validate_profile_data(self, data: dict, username: str) -> bool:
        """Validate profile data structure"""
        if not data or 'data' not in data or 'user' not in data['data']:
            error_msg = f'Invalid profile data structure for {username}'
            current_app.logger.error(error_msg)
            self.proxy_session.record_failure()
            return False
        return True

    def _validate_stories_data(self, data: dict, username: str, user_id: str) -> bool:
        """Validate stories data structure"""
        if not data or 'reels' not in data or user_id not in data['reels']:
            error_msg = f'Invalid stories data structure for {username}'
            current_app.logger.error(error_msg)
            self.proxy_session.record_failure()
            return False
        return True

    async def cleanup(self) -> None:
        """Clean up resources"""
        if self.session:
            current_app.logger.debug(f'Closing aiohttp session for proxy {self.proxy_session.proxy_url_safe}')
            await self.session.close()
            self.session = None
