"""
Media Analyzer Module

Analyzes media items and categorizes them based on configured criteria.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn


class MediaAnalyzer:
    """Analyzes and categorizes media items for potential purging"""

    def __init__(self, plex_client, tautulli_client, thresholds: Dict):
        """
        Initialize MediaAnalyzer

        Args:
            plex_client: PlexClient instance
            tautulli_client: TautulliClient instance
            thresholds: Dictionary of threshold values
        """
        self.plex = plex_client
        self.tautulli = tautulli_client
        self.thresholds = thresholds

    def analyze_media(self, media_items: List[Dict], show_progress: bool = True) -> Dict[str, List[Dict]]:
        """
        Analyze media items and categorize them

        Args:
            media_items: List of media item dictionaries from Plex
            show_progress: Whether to show progress bar

        Returns:
            Dictionary with categorized media items
        """
        categories = {
            'cat1_5years': {'movies': [], 'shows': []},
            'cat2_3years': {'movies': [], 'shows': []},
            'cat3_1year': {'movies': [], 'shows': []},
            'cat4_large_movies': {'movies': [], 'shows': []},
            'cat5_large_shows': {'movies': [], 'shows': []},
        }

        processed_items = set()  # Track items to prevent duplicates

        # Calculate cutoff dates
        now = datetime.now()
        cutoff_5years = now - timedelta(days=self.thresholds['old_5years'])
        cutoff_3years = now - timedelta(days=self.thresholds['old_3years'])
        cutoff_1year = now - timedelta(days=self.thresholds['old_1year'])

        if show_progress:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            ) as progress:
                task = progress.add_task("Analyzing media items...", total=len(media_items))

                for item in media_items:
                    self._categorize_item(
                        item, categories, processed_items,
                        cutoff_5years, cutoff_3years, cutoff_1year
                    )
                    progress.update(task, advance=1)
        else:
            for item in media_items:
                self._categorize_item(
                    item, categories, processed_items,
                    cutoff_5years, cutoff_3years, cutoff_1year
                )

        return categories

    def _categorize_item(self, item: Dict, categories: Dict, processed_items: set,
                        cutoff_5years: datetime, cutoff_3years: datetime, cutoff_1year: datetime):
        """
        Categorize a single media item (priority order)

        Args:
            item: Media item dictionary
            categories: Categories dictionary to populate
            processed_items: Set of already processed item IDs
            cutoff_5years: 5-year cutoff datetime
            cutoff_3years: 3-year cutoff datetime
            cutoff_1year: 1-year cutoff datetime
        """
        rating_key = item['rating_key']

        # Skip if already categorized
        if rating_key in processed_items:
            return

        # Get watch history from Tautulli (pass media type for proper TV show handling)
        media_type = item['type']
        watch_info = self.tautulli.get_watch_history(str(rating_key), media_type)

        # Enrich item with watch data
        enriched_item = {
            **item,
            'watched': watch_info['watched'],
            'watch_status': watch_info['watch_status'],
            'watch_count': watch_info['watch_count'],
            'users_watched': watch_info['users'],
            'user_progress': watch_info['user_progress'],
            'last_watched': watch_info['last_watched']
        }

        added_at = item['added_at']
        size_gb = item['size_gb']
        media_type = item['type']

        # Determine media category (movie vs show)
        category_type = 'movies' if media_type == 'movie' else 'shows'

        # Priority order categorization (first match wins)

        # Category 1: Added > 5 years ago
        if added_at and added_at < cutoff_5years:
            categories['cat1_5years'][category_type].append(enriched_item)
            processed_items.add(rating_key)
            return

        # Category 2: Added > 3 years ago
        if added_at and added_at < cutoff_3years:
            categories['cat2_3years'][category_type].append(enriched_item)
            processed_items.add(rating_key)
            return

        # Category 3: Added > 1 year ago
        if added_at and added_at < cutoff_1year:
            categories['cat3_1year'][category_type].append(enriched_item)
            processed_items.add(rating_key)
            return

        # Category 4: Large movies (> 30GB)
        if media_type == 'movie' and size_gb > self.thresholds['large_movie']:
            categories['cat4_large_movies'][category_type].append(enriched_item)
            processed_items.add(rating_key)
            return

        # Category 5: Large TV series (> 100GB)
        if media_type == 'show' and size_gb > self.thresholds['large_series']:
            categories['cat5_large_shows'][category_type].append(enriched_item)
            processed_items.add(rating_key)
            return

    def get_category_stats(self, categories: Dict) -> Dict:
        """
        Get statistics for all categories

        Args:
            categories: Categorized media dictionary

        Returns:
            Dictionary with category statistics
        """
        stats = {}

        for cat_key, cat_data in categories.items():
            movies = cat_data['movies']
            shows = cat_data['shows']

            total_items = len(movies) + len(shows)
            total_size = sum(item['size_gb'] for item in movies + shows)

            stats[cat_key] = {
                'total_items': total_items,
                'movie_count': len(movies),
                'show_count': len(shows),
                'total_size_gb': total_size
            }

        return stats

    def sort_items(self, items: List[Dict], by_size: bool = True) -> List[Dict]:
        """
        Sort media items

        Args:
            items: List of media items
            by_size: If True, sort by size (largest first), else by date added (oldest first)

        Returns:
            Sorted list of items
        """
        if by_size:
            return sorted(items, key=lambda x: x['size_gb'], reverse=True)
        else:
            return sorted(items, key=lambda x: x['added_at'] if x['added_at'] else datetime.min)
