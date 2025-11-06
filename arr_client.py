"""
Sonarr/Radarr API Client Module

Handles interactions with Sonarr and Radarr APIs for media lookup with caching support.
"""

import requests
import json
import os
from typing import Optional, Dict
from datetime import datetime, timedelta


class ArrClient:
    """Client for Sonarr and Radarr APIs with caching support"""

    def __init__(self, sonarr_url: str = None, sonarr_api_key: str = None,
                 radarr_url: str = None, radarr_api_key: str = None,
                 cache_file: str = 'output/arr_cache.json'):
        """
        Initialize the Arr client with optional Sonarr and Radarr configurations.

        Args:
            sonarr_url: Base URL for Sonarr instance
            sonarr_api_key: API key for Sonarr
            radarr_url: Base URL for Radarr instance
            radarr_api_key: API key for Radarr
            cache_file: Path to JSON file for caching API results
        """
        self.sonarr_url = sonarr_url.rstrip('/') if sonarr_url else None
        self.sonarr_api_key = sonarr_api_key
        self.radarr_url = radarr_url.rstrip('/') if radarr_url else None
        self.radarr_api_key = radarr_api_key
        self.cache_file = cache_file
        self.cache = self._load_cache()
        self.sonarr_connected = False
        self.radarr_connected = False

        # Test connections
        if self.sonarr_url and self.sonarr_api_key:
            self.sonarr_connected = self._test_sonarr_connection()

        if self.radarr_url and self.radarr_api_key:
            self.radarr_connected = self._test_radarr_connection()

    def _load_cache(self) -> Dict:
        """Load cache from file if it exists"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load arr cache: {e}")
        return {'sonarr': {}, 'radarr': {}, 'last_updated': None}

    def _save_cache(self):
        """Save cache to file"""
        try:
            self.cache['last_updated'] = datetime.now().isoformat()
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not save arr cache: {e}")

    def _test_sonarr_connection(self) -> bool:
        """Test connection to Sonarr API"""
        try:
            headers = {'X-Api-Key': self.sonarr_api_key}
            url = f"{self.sonarr_url}/api/v3/system/status"
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            return True
        except Exception:
            return False

    def _test_radarr_connection(self) -> bool:
        """Test connection to Radarr API"""
        try:
            headers = {'X-Api-Key': self.radarr_api_key}
            url = f"{self.radarr_url}/api/v3/system/status"
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            return True
        except Exception:
            return False

    def get_connection_status(self) -> Dict[str, bool]:
        """Get connection status for both services"""
        return {
            'sonarr': self.sonarr_connected,
            'radarr': self.radarr_connected
        }

    def get_sonarr_series(self, tvdb_id: str) -> Optional[Dict]:
        """
        Look up series in Sonarr by TVDB ID.

        Args:
            tvdb_id: TVDB ID of the series

        Returns:
            Series data dict or None if not found
        """
        if not self.sonarr_url or not self.sonarr_api_key or not tvdb_id:
            return None

        # Check cache first
        cache_key = f"tvdb_{tvdb_id}"
        if cache_key in self.cache['sonarr']:
            return self.cache['sonarr'][cache_key]

        # If not connected, return None (cached lookups still work above)
        if not self.sonarr_connected:
            return None

        try:
            headers = {'X-Api-Key': self.sonarr_api_key}
            url = f"{self.sonarr_url}/api/v3/series"
            params = {'tvdbId': tvdb_id}

            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            series_list = response.json()
            if series_list and len(series_list) > 0:
                series_data = series_list[0]
                # Cache the result
                self.cache['sonarr'][cache_key] = series_data
                self._save_cache()
                return series_data

            # Cache negative result (not found)
            self.cache['sonarr'][cache_key] = None
            self._save_cache()
            return None

        except Exception as e:
            print(f"Warning: Error looking up series in Sonarr (TVDB: {tvdb_id}): {e}")
            return None

    def get_radarr_movie(self, tmdb_id: str = None, imdb_id: str = None) -> Optional[Dict]:
        """
        Look up movie in Radarr by TMDB or IMDB ID.

        Args:
            tmdb_id: TMDB ID of the movie
            imdb_id: IMDB ID of the movie

        Returns:
            Movie data dict or None if not found
        """
        if not self.radarr_url or not self.radarr_api_key:
            return None
        if not tmdb_id and not imdb_id:
            return None

        # Check cache first (prefer TMDB ID)
        cache_key = f"tmdb_{tmdb_id}" if tmdb_id else f"imdb_{imdb_id}"
        if cache_key in self.cache['radarr']:
            return self.cache['radarr'][cache_key]

        # If not connected, return None (cached lookups still work above)
        if not self.radarr_connected:
            return None

        try:
            headers = {'X-Api-Key': self.radarr_api_key}
            url = f"{self.radarr_url}/api/v3/movie"

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            movies = response.json()

            # Search for matching movie
            for movie in movies:
                if tmdb_id and str(movie.get('tmdbId')) == str(tmdb_id):
                    # Cache the result
                    self.cache['radarr'][cache_key] = movie
                    self._save_cache()
                    return movie
                if imdb_id and movie.get('imdbId') == imdb_id:
                    # Cache the result
                    self.cache['radarr'][cache_key] = movie
                    self._save_cache()
                    return movie

            # Cache negative result (not found)
            self.cache['radarr'][cache_key] = None
            self._save_cache()
            return None

        except Exception as e:
            id_str = f"TMDB: {tmdb_id}" if tmdb_id else f"IMDB: {imdb_id}"
            print(f"Warning: Error looking up movie in Radarr ({id_str}): {e}")
            return None

    def get_sonarr_url(self, tvdb_id: str) -> Optional[str]:
        """
        Get Sonarr web UI URL for a series.

        Args:
            tvdb_id: TVDB ID of the series

        Returns:
            Full URL to series page in Sonarr or None
        """
        series = self.get_sonarr_series(tvdb_id)
        if series and 'titleSlug' in series:
            return f"{self.sonarr_url}/series/{series['titleSlug']}"
        return None

    def get_radarr_url(self, tmdb_id: str = None, imdb_id: str = None) -> Optional[str]:
        """
        Get Radarr web UI URL for a movie.

        Args:
            tmdb_id: TMDB ID of the movie
            imdb_id: IMDB ID of the movie

        Returns:
            Full URL to movie page in Radarr or None
        """
        movie = self.get_radarr_movie(tmdb_id, imdb_id)
        if movie and 'titleSlug' in movie:
            return f"{self.radarr_url}/movie/{movie['titleSlug']}"
        return None
