"""
Plex API Client Module

Handles all interactions with the Plex Media Server API using PlexAPI library.
"""

from plexapi.server import PlexServer
from plexapi.exceptions import NotFound, Unauthorized
from datetime import datetime
from typing import List, Dict, Optional
import sys


class PlexClient:
    """Client for interacting with Plex Media Server"""

    def __init__(self, plex_url: str, plex_token: str):
        """
        Initialize Plex client

        Args:
            plex_url: URL of the Plex server
            plex_token: Authentication token for Plex
        """
        self.plex_url = plex_url
        self.plex_token = plex_token
        self.plex = None

    def connect(self) -> bool:
        """
        Connect to Plex server

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.plex = PlexServer(self.plex_url, self.plex_token)
            return True
        except Unauthorized:
            print(f"Error: Invalid Plex token. Please check your PLEX_TOKEN in config.py")
            return False
        except Exception as e:
            print(f"Error connecting to Plex server: {e}")
            return False

    def get_server_name(self) -> str:
        """Get the friendly name of the Plex server"""
        if self.plex:
            return self.plex.friendlyName
        return "Unknown"

    def get_server_id(self) -> str:
        """Get the machine identifier of the Plex server"""
        if self.plex:
            return self.plex.machineIdentifier
        return None

    def get_libraries(self, excluded_libraries: List[str] = None) -> List[Dict]:
        """
        Get all libraries from Plex server

        Args:
            excluded_libraries: List of library names to exclude

        Returns:
            List of library dictionaries with name and type
        """
        if not self.plex:
            return []

        excluded_libraries = excluded_libraries or []
        libraries = []

        for section in self.plex.library.sections():
            if section.title not in excluded_libraries:
                # Only include movie and TV show libraries
                if section.type in ['movie', 'show']:
                    libraries.append({
                        'name': section.title,
                        'type': section.type,
                        'section': section
                    })

        return libraries

    def get_media_items(self, library_name: str) -> List[Dict]:
        """
        Get all media items from a library with metadata

        Args:
            library_name: Name of the library

        Returns:
            List of media item dictionaries
        """
        if not self.plex:
            return []

        try:
            library = self.plex.library.section(library_name)
        except NotFound:
            print(f"Warning: Library '{library_name}' not found")
            return []

        media_items = []

        for item in library.all():
            media_data = self._extract_media_data(item, library.type)
            if media_data:
                media_items.append(media_data)

        return media_items

    def _extract_media_data(self, item, library_type: str) -> Optional[Dict]:
        """
        Extract metadata from a media item

        Args:
            item: Plex media item object
            library_type: Type of library ('movie' or 'show')

        Returns:
            Dictionary with media metadata
        """
        try:
            # Calculate total file size
            total_size = 0
            file_paths = []

            if library_type == 'show':
                # For TV shows, sum up all episodes
                for episode in item.episodes():
                    for media in episode.media:
                        for part in media.parts:
                            total_size += part.size
                            file_paths.append(part.file)
            else:
                # For movies
                for media in item.media:
                    for part in media.parts:
                        total_size += part.size
                        file_paths.append(part.file)

            # Convert bytes to GB
            size_gb = total_size / (1024 ** 3)

            # Get added date
            added_at = item.addedAt if hasattr(item, 'addedAt') else None

            # Get view count from Plex (basic tracking)
            view_count = item.viewCount if hasattr(item, 'viewCount') and item.viewCount else 0

            return {
                'title': item.title,
                'year': item.year if hasattr(item, 'year') else None,
                'rating_key': item.ratingKey,  # Unique Plex ID
                'added_at': added_at,
                'size_bytes': total_size,
                'size_gb': size_gb,
                'file_paths': file_paths,
                'type': library_type,
                'view_count': view_count,
                'guid': item.guid if hasattr(item, 'guid') else None,
            }

        except Exception as e:
            print(f"Warning: Error extracting data for {item.title}: {e}")
            return None

    def get_library_stats(self, library_name: str) -> Dict:
        """
        Get statistics for a library

        Args:
            library_name: Name of the library

        Returns:
            Dictionary with library statistics
        """
        if not self.plex:
            return {}

        try:
            library = self.plex.library.section(library_name)
            items = library.all()

            return {
                'name': library_name,
                'type': library.type,
                'total_items': len(items),
            }
        except NotFound:
            return {}
