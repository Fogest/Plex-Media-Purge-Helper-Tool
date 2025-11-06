"""
Tautulli API Client Module

Handles all interactions with the Tautulli API for watch history and statistics.
"""

import requests
from typing import Dict, List, Optional
from datetime import datetime


class TautulliClient:
    """Client for interacting with Tautulli API"""

    def __init__(self, tautulli_url: str, api_key: str):
        """
        Initialize Tautulli client

        Args:
            tautulli_url: URL of the Tautulli server
            api_key: API key for Tautulli
        """
        self.tautulli_url = tautulli_url.rstrip('/')
        self.api_key = api_key
        self.api_endpoint = f"{self.tautulli_url}/api/v2"

    def test_connection(self) -> bool:
        """
        Test connection to Tautulli server

        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = self._make_request('get_server_info')
            return response is not None
        except Exception as e:
            print(f"Error connecting to Tautulli: {e}")
            return False

    def _make_request(self, cmd: str, params: Dict = None) -> Optional[Dict]:
        """
        Make a request to the Tautulli API

        Args:
            cmd: API command to execute
            params: Additional parameters for the request

        Returns:
            Response data or None if request failed
        """
        request_params = {
            'apikey': self.api_key,
            'cmd': cmd
        }

        if params:
            request_params.update(params)

        try:
            response = requests.get(self.api_endpoint, params=request_params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if data.get('response', {}).get('result') == 'success':
                return data.get('response', {}).get('data')
            else:
                print(f"Tautulli API error for command '{cmd}': {data.get('response', {}).get('message', 'Unknown error')}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Error making Tautulli request for '{cmd}': {e}")
            return None
        except ValueError as e:
            print(f"Error parsing Tautulli JSON response: {e}")
            return None

    def get_watch_history(self, rating_key: str, media_type: str = 'movie') -> Dict:
        """
        Get watch history for a specific media item with per-user progress tracking

        Args:
            rating_key: Plex rating key (unique ID) for the media item
            media_type: Type of media ('movie' or 'show')

        Returns:
            Dictionary with watch history information including per-user progress
        """
        # For TV shows, get metadata and children (episodes) for watch data
        if media_type == 'show':
            return self._get_show_watch_history(rating_key)

        # For movies, use the standard history query
        params = {
            'rating_key': rating_key,
            'length': 1000,  # Get up to 1000 watch records
            'order_column': 'date',
            'order_dir': 'desc'
        }

        data = self._make_request('get_history', params)

        if not data:
            return {
                'watched': False,
                'watch_status': 'unwatched',
                'watch_count': 0,
                'users': [],
                'user_progress': {},
                'last_watched': None
            }

        # Track per-user watch progress
        user_progress = {}  # {username: max_percent_complete}
        watch_count = data.get('recordsFiltered', 0)
        last_watched = None

        if watch_count > 0:
            records = data.get('data', [])

            for record in records:
                user_name = record.get('friendly_name', record.get('user', 'Unknown'))
                percent_complete = record.get('percent_complete', 0)

                # Track the highest completion percentage per user
                if user_name not in user_progress or percent_complete > user_progress[user_name]:
                    user_progress[user_name] = percent_complete

                # Get the most recent watch date (from any user)
                if not last_watched and record.get('date'):
                    try:
                        last_watched = datetime.fromtimestamp(record['date'])
                    except (ValueError, TypeError):
                        pass

        # Determine overall watch status
        fully_watched_users = [user for user, progress in user_progress.items() if progress >= 80]
        in_progress_users = [user for user, progress in user_progress.items() if 1 <= progress < 80]

        if fully_watched_users:
            watch_status = 'watched'
        elif in_progress_users or any(progress > 0 for progress in user_progress.values()):
            watch_status = 'in_progress'
        else:
            watch_status = 'unwatched'

        return {
            'watched': len(fully_watched_users) > 0,
            'watch_status': watch_status,  # 'watched', 'in_progress', or 'unwatched'
            'watch_count': watch_count,
            'users': sorted(list(user_progress.keys())),
            'user_progress': user_progress,  # {username: percent_complete}
            'last_watched': last_watched
        }

    def _get_show_watch_history(self, rating_key: str) -> Dict:
        """
        Get watch history for a TV show by aggregating episode watch data

        Args:
            rating_key: Plex rating key for the TV show

        Returns:
            Dictionary with aggregated watch history for the show
        """
        # First, get metadata which includes user watch statistics
        metadata_params = {
            'rating_key': rating_key
        }
        metadata = self._make_request('get_metadata', params=metadata_params)

        if not metadata:
            return {
                'watched': False,
                'watch_status': 'unwatched',
                'watch_count': 0,
                'users': [],
                'user_progress': {},
                'last_watched': None
            }

        # Get user watch info from metadata - this includes aggregated watch stats
        user_rating = metadata.get('user_rating')
        play_count = metadata.get('play_count', 0)
        last_played = metadata.get('last_played')

        # Parse last_watched date
        last_watched = None
        if last_played:
            try:
                last_watched = datetime.fromtimestamp(last_played)
            except (ValueError, TypeError):
                pass

        # Initialize tracking
        user_progress = {}
        user_episodes_watched = {}

        # Query episode history to get accurate per-episode watch data
        # This is more accurate than user stats which count total plays (including rewatches)
        # Get all history records (no rating_key filter initially)
        history_params = {
            'length': 10000,
            'media_type': 'episode',
            'order_column': 'date',
            'order_dir': 'desc'
        }

        data = self._make_request('get_history', params=history_params)

        if data and data.get('recordsFiltered', 0) > 0:
            records = data.get('data', [])

            # Track per-user episode watches for this show
            user_episodes_watched_set = {}  # {username: set of episode rating keys}
            user_episodes_in_progress_set = {}  # {username: set of in-progress episodes}
            all_episodes_seen = set()  # Track ALL unique episodes for this show to calculate total
            matched_records = 0

            for record in records:
                # Check if this episode belongs to our show
                record_grandparent_key = record.get('grandparent_rating_key', '')

                if str(record_grandparent_key) != str(rating_key):
                    continue  # Skip episodes from other shows

                matched_records += 1

                user_name = record.get('friendly_name', record.get('user', 'Unknown'))
                percent_complete = record.get('percent_complete', 0)
                episode_rating_key = record.get('rating_key')

                if not episode_rating_key:
                    continue

                # Track this episode in the set of all episodes seen for this show
                all_episodes_seen.add(episode_rating_key)

                # Initialize user tracking sets
                if user_name not in user_episodes_watched_set:
                    user_episodes_watched_set[user_name] = set()
                    user_episodes_in_progress_set[user_name] = set()

                # Track watched episodes (>= 80%)
                if percent_complete >= 80:
                    user_episodes_watched_set[user_name].add(episode_rating_key)
                    user_episodes_in_progress_set[user_name].discard(episode_rating_key)
                elif percent_complete > 0:
                    if episode_rating_key not in user_episodes_watched_set[user_name]:
                        user_episodes_in_progress_set[user_name].add(episode_rating_key)

                # Track last watched
                if not last_watched and record.get('date'):
                    try:
                        record_date = datetime.fromtimestamp(record['date'])
                        if not last_watched or record_date > last_watched:
                            last_watched = record_date
                    except (ValueError, TypeError):
                        pass

            # Use the count of all unique episodes that have been seen (watched or in-progress) as total
            # This is more reliable than metadata fields which may not be populated
            total_episodes = len(all_episodes_seen)

            # Calculate per-user progress
            for user_name in user_episodes_watched_set.keys():
                episodes_watched = len(user_episodes_watched_set[user_name])
                user_episodes_watched[user_name] = episodes_watched

                if total_episodes > 0:
                    progress_pct = int((episodes_watched / total_episodes) * 100)
                else:
                    # Fallback calculation (should rarely hit this now)
                    total_user_episodes = episodes_watched + len(user_episodes_in_progress_set.get(user_name, set()))
                    progress_pct = int((episodes_watched / total_user_episodes) * 100) if total_user_episodes > 0 else 0

                user_progress[user_name] = min(progress_pct, 100)

        # Determine overall watch status
        fully_watched_users = [user for user, progress in user_progress.items() if progress >= 80]
        in_progress_users = [user for user, progress in user_progress.items() if 1 <= progress < 80]

        if fully_watched_users:
            watch_status = 'watched'
        elif in_progress_users or user_progress:
            watch_status = 'in_progress'
        else:
            watch_status = 'unwatched'

        watch_count = sum(user_episodes_watched.values()) if user_episodes_watched else play_count

        return {
            'watched': len(fully_watched_users) > 0,
            'watch_status': watch_status,
            'watch_count': watch_count,
            'users': sorted(list(user_progress.keys())),
            'user_progress': user_progress,
            'last_watched': last_watched
        }

    def get_item_watch_stats(self, rating_key: str) -> Dict:
        """
        Get detailed watch statistics for a media item

        Args:
            rating_key: Plex rating key for the media item

        Returns:
            Dictionary with watch statistics
        """
        params = {
            'rating_key': rating_key
        }

        data = self._make_request('get_metadata', params)

        if not data:
            return {}

        return {
            'play_count': data.get('play_count', 0),
            'last_played': data.get('last_played'),
            'users_watched': data.get('users_watched', [])
        }

    def get_libraries(self) -> List[Dict]:
        """
        Get all libraries from Tautulli

        Returns:
            List of library dictionaries
        """
        data = self._make_request('get_libraries')

        if not data:
            return []

        return data

    def get_server_info(self) -> Dict:
        """
        Get Tautulli server information

        Returns:
            Dictionary with server info
        """
        data = self._make_request('get_server_info')
        return data if data else {}
