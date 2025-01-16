"""
Test StoryChecker with real Instagram profiles
"""

import asyncio
from core.story_checker import SimpleStoryChecker, StoryChecker

async def check_profile(username: str) -> None:
    """Check a specific Instagram profile for stories
    
    Args:
        username: Instagram username to check
    """
    # Use the session cookie with no proxy for testing
    session_cookie = "2238026741%3A2rpKY2FiA7k4I8%3A25%3AAYfQ4F7VzR5yDSaFCG93P6hjLmGCdHPctpasHa8-3Q"
    checker = StoryChecker(proxy=None, session_cookie=session_cookie)
    
    try:
        print(f"\nChecking @{username}...")
        has_story = await checker.check_profile(username)
        print(f"\nHas story: {has_story}")
        print(f"Success rate: {checker.pair.success_rate:.2%}")
        print(f"Total checks: {checker.pair.total_checks}")
        print(f"Last check: {checker.checker.last_check}")
    except Exception as e:
        print(f"\nError: {str(e)}")
    finally:
        await checker.checker.cleanup()

async def main():
    """Test known profiles"""
    # Profile that should have a story
    await check_profile("shordyslickk")
    
    # Add longer delay between requests
    await asyncio.sleep(5)
    
    # Profile that should not have a story
    await check_profile("tooprettyriah")

if __name__ == "__main__":
    asyncio.run(main())
