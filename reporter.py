"""
Reporter Module

Generates output reports in various formats (terminal, markdown, HTML).
"""

from typing import Dict, List
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
import os


class Reporter:
    """Generates reports from categorized media data"""

    CATEGORY_NAMES = {
        'cat1_5years': 'Category 1: Added Over 5 Years Ago',
        'cat2_3years': 'Category 2: Added Over 3 Years Ago',
        'cat3_1year': 'Category 3: Added Over 1 Year Ago',
        'cat4_large_movies': 'Category 4: Large Movies (Over 30GB)',
        'cat5_large_shows': 'Category 5: Large TV Series (Over 100GB)',
    }

    def __init__(self, output_dir: str = 'output', plex_url: str = None, tautulli_url: str = None, plex_server_id: str = None, arr_client=None):
        """
        Initialize Reporter

        Args:
            output_dir: Directory for output files
            plex_url: Plex server URL for generating links
            tautulli_url: Tautulli server URL for generating links
            plex_server_id: Plex server machine identifier
            arr_client: ArrClient instance for Sonarr/Radarr integration
        """
        self.output_dir = output_dir
        self.plex_url = plex_url.rstrip('/') if plex_url else None
        self.tautulli_url = tautulli_url.rstrip('/') if tautulli_url else None
        self.plex_server_id = plex_server_id
        self.arr_client = arr_client
        self.console = Console()

    def _get_plex_web_url(self, rating_key: str, media_type: str) -> str:
        """
        Generate Plex Web App URL for a media item

        Args:
            rating_key: Plex rating key
            media_type: Type of media ('movie' or 'show')

        Returns:
            Plex web URL
        """
        if not self.plex_url or not rating_key or not self.plex_server_id:
            return None
        # Plex Web App URL format
        return f"{self.plex_url}/web/index.html#!/server/{self.plex_server_id}/details?key=%2Flibrary%2Fmetadata%2F{rating_key}"

    def _get_tautulli_url(self, rating_key: str) -> str:
        """
        Generate Tautulli URL for a media item

        Args:
            rating_key: Plex rating key

        Returns:
            Tautulli URL
        """
        if not self.tautulli_url or not rating_key:
            return None
        return f"{self.tautulli_url}/info?rating_key={rating_key}"

    def _get_sonarr_url(self, tvdb_id: str) -> str:
        """
        Generate Sonarr URL for a TV show

        Args:
            tvdb_id: TVDB ID of the series

        Returns:
            Sonarr URL or None
        """
        if not self.arr_client or not tvdb_id:
            return None
        return self.arr_client.get_sonarr_url(tvdb_id)

    def _get_radarr_url(self, tmdb_id: str = None, imdb_id: str = None) -> str:
        """
        Generate Radarr URL for a movie

        Args:
            tmdb_id: TMDB ID of the movie
            imdb_id: IMDB ID of the movie

        Returns:
            Radarr URL or None
        """
        if not self.arr_client:
            return None
        return self.arr_client.get_radarr_url(tmdb_id, imdb_id)

    def _prefetch_arr_urls(self, categories: Dict):
        """
        Pre-fetch Sonarr/Radarr URLs for all items with progress indicator

        Args:
            categories: Categorized media dictionary
        """
        if not self.arr_client:
            return

        from rich.progress import Progress, SpinnerColumn, TextColumn

        # Count total items that need lookup
        total_items = 0
        for cat_data in categories.values():
            for item in cat_data['movies']:
                if item.get('tmdb_id') or item.get('imdb_id'):
                    total_items += 1
            for item in cat_data['shows']:
                if item.get('tvdb_id'):
                    total_items += 1

        if total_items == 0:
            return

        self.console.print("[cyan]Fetching Sonarr/Radarr links...[/cyan]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task(f"Looking up {total_items} items...", total=total_items)

            for cat_data in categories.values():
                # Pre-fetch movie URLs
                for item in cat_data['movies']:
                    if item.get('tmdb_id') or item.get('imdb_id'):
                        self._get_radarr_url(item.get('tmdb_id'), item.get('imdb_id'))
                        progress.advance(task)

                # Pre-fetch show URLs
                for item in cat_data['shows']:
                    if item.get('tvdb_id'):
                        self._get_sonarr_url(item['tvdb_id'])
                        progress.advance(task)

        self.console.print("[green]✓[/green] Arr links fetched")
        self.console.print()

    def generate_report(self, categories: Dict, stats: Dict, format: str = 'terminal'):
        """
        Generate report in specified format

        Args:
            categories: Categorized media dictionary
            stats: Category statistics dictionary
            format: Output format ('terminal', 'markdown', 'html', 'all')
        """
        # Pre-fetch arr URLs if generating markdown or html (not needed for terminal)
        if (format == 'markdown' or format == 'html' or format == 'all') and self.arr_client:
            self._prefetch_arr_urls(categories)

        if format == 'terminal' or format == 'all':
            self.print_terminal_report(categories, stats)

        if format == 'markdown' or format == 'all':
            self.generate_markdown_report(categories, stats)

        if format == 'html' or format == 'all':
            self.generate_html_report(categories, stats)

    def print_terminal_report(self, categories: Dict, stats: Dict):
        """
        Print report to terminal using Rich

        Args:
            categories: Categorized media dictionary
            stats: Category statistics dictionary
        """
        self.console.print()
        self.console.print(Panel.fit(
            "[bold cyan]Plex Media Purge Analysis Report[/bold cyan]",
            border_style="cyan"
        ))
        self.console.print()

        # Overall summary
        total_items = sum(s['total_items'] for s in stats.values())
        total_size = sum(s['total_size_gb'] for s in stats.values())

        self.console.print(f"[bold]Total Items Found:[/bold] {total_items}")
        self.console.print(f"[bold]Total Size:[/bold] {total_size:.2f} GB")
        self.console.print()

        # Print each category
        for cat_key in ['cat1_5years', 'cat2_3years', 'cat3_1year', 'cat4_large_movies', 'cat5_large_shows']:
            cat_data = categories[cat_key]
            cat_stats = stats[cat_key]

            if cat_stats['total_items'] > 0:
                self._print_category(cat_key, cat_data, cat_stats)

    def _print_category(self, cat_key: str, cat_data: Dict, cat_stats: Dict):
        """
        Print a single category to terminal

        Args:
            cat_key: Category key
            cat_data: Category media data
            cat_stats: Category statistics
        """
        category_name = self.CATEGORY_NAMES[cat_key]

        self.console.print(f"\n[bold yellow]{category_name}[/bold yellow]")
        self.console.print("=" * 80)
        self.console.print(f"Total: {cat_stats['total_items']} items, {cat_stats['total_size_gb']:.2f} GB\n")

        # Print movies
        if cat_data['movies']:
            self.console.print(f"[bold cyan]MOVIES[/bold cyan] ({len(cat_data['movies'])} items)")
            self._print_media_table(cat_data['movies'])
            self.console.print()

        # Print TV shows
        if cat_data['shows']:
            self.console.print(f"[bold magenta]TV SHOWS[/bold magenta] ({len(cat_data['shows'])} items)")
            self._print_media_table(cat_data['shows'])
            self.console.print()

    def _print_media_table(self, items: List[Dict]):
        """
        Print media items as a table

        Args:
            items: List of media items
        """
        table = Table(show_header=True, header_style="bold")
        table.add_column("Title", style="cyan", width=35)
        table.add_column("Size", justify="right", width=10)
        table.add_column("Added", width=12)
        table.add_column("Status", justify="center", width=12)
        table.add_column("Watched By (Progress)", width=40)
        table.add_column("Last Watched", width=12)

        for item in items:
            title = item['title']
            if item.get('year'):
                title = f"{title} ({item['year']})"

            size = f"{item['size_gb']:.2f} GB"
            added = item['added_at'].strftime('%Y-%m-%d') if item['added_at'] else 'N/A'

            # Determine watch status icon and text
            watch_status = item.get('watch_status', 'unwatched')
            if watch_status == 'watched':
                status_display = "[green]✓ Watched[/green]"
            elif watch_status == 'in_progress':
                status_display = "[yellow]◐ In Progress[/yellow]"
            else:
                status_display = "[red]✗ Unwatched[/red]"

            # Build user list with progress percentages
            user_progress = item.get('user_progress', {})
            if user_progress:
                user_list = []
                for user in sorted(user_progress.keys()):
                    progress = user_progress[user]
                    if progress >= 80:
                        user_list.append(f"{user} (100%)")
                    elif progress > 0:
                        user_list.append(f"{user} ({int(progress)}%)")
                    else:
                        user_list.append(f"{user} (0%)")
                users_display = ', '.join(user_list)
            else:
                users_display = '-'

            last_watched = item['last_watched'].strftime('%Y-%m-%d') if item['last_watched'] else '-'

            table.add_row(title, size, added, status_display, users_display, last_watched)

        self.console.print(table)

    def generate_markdown_report(self, categories: Dict, stats: Dict):
        """
        Generate markdown report file

        Args:
            categories: Categorized media dictionary
            stats: Category statistics dictionary
        """
        os.makedirs(self.output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(self.output_dir, f'plex_purge_report_{timestamp}.md')

        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# Plex Media Purge Analysis Report\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # Summary
            total_items = sum(s['total_items'] for s in stats.values())
            total_size = sum(s['total_size_gb'] for s in stats.values())

            f.write("## Summary\n\n")
            f.write(f"- **Total Items Found:** {total_items}\n")
            f.write(f"- **Total Size:** {total_size:.2f} GB\n\n")

            # Categories
            for cat_key in ['cat1_5years', 'cat2_3years', 'cat3_1year', 'cat4_large_movies', 'cat5_large_shows']:
                cat_data = categories[cat_key]
                cat_stats = stats[cat_key]

                if cat_stats['total_items'] > 0:
                    self._write_markdown_category(f, cat_key, cat_data, cat_stats)

        self.console.print(f"[green]Markdown report saved to: {filename}[/green]")

    def _write_markdown_category(self, f, cat_key: str, cat_data: Dict, cat_stats: Dict):
        """
        Write a category to markdown file

        Args:
            f: File object
            cat_key: Category key
            cat_data: Category media data
            cat_stats: Category statistics
        """
        category_name = self.CATEGORY_NAMES[cat_key]

        f.write(f"## {category_name}\n\n")
        f.write(f"**Total:** {cat_stats['total_items']} items, {cat_stats['total_size_gb']:.2f} GB\n\n")

        # Movies
        if cat_data['movies']:
            f.write(f"### MOVIES ({len(cat_data['movies'])} items)\n\n")
            self._write_markdown_table(f, cat_data['movies'])

        # TV Shows
        if cat_data['shows']:
            f.write(f"### TV SHOWS ({len(cat_data['shows'])} items)\n\n")
            self._write_markdown_table(f, cat_data['shows'])

    def _write_markdown_table(self, f, items: List[Dict]):
        """
        Write media items as markdown table

        Args:
            f: File object
            items: List of media items
        """
        f.write("| Title | Size | Added | Status | Watched By (Progress) | Last Watched |\n")
        f.write("|-------|------|-------|--------|----------------------|-------------|\n")

        for item in items:
            # Build title with links
            title = item['title']
            if item.get('year'):
                title = f"{title} ({item['year']})"

            # Create Plex link (title becomes clickable)
            plex_url = self._get_plex_web_url(str(item['rating_key']), item['type'])
            if plex_url:
                title = f"[{title}]({plex_url})"

            # Add Tautulli link as (T)
            tautulli_url = self._get_tautulli_url(str(item['rating_key']))
            if tautulli_url:
                title = f"{title} [(T)]({tautulli_url})"

            # Add Sonarr link as (S) for TV shows
            if item['type'] == 'show' and item.get('tvdb_id'):
                sonarr_url = self._get_sonarr_url(item['tvdb_id'])
                if sonarr_url:
                    title = f"{title} [(S)]({sonarr_url})"

            # Add Radarr link as (R) for movies
            if item['type'] == 'movie' and (item.get('tmdb_id') or item.get('imdb_id')):
                radarr_url = self._get_radarr_url(item.get('tmdb_id'), item.get('imdb_id'))
                if radarr_url:
                    title = f"{title} [(R)]({radarr_url})"

            size = f"{item['size_gb']:.2f} GB"
            added = item['added_at'].strftime('%Y-%m-%d') if item['added_at'] else 'N/A'

            # Watch status
            watch_status = item.get('watch_status', 'unwatched')
            if watch_status == 'watched':
                status = "✓ Watched"
            elif watch_status == 'in_progress':
                status = "◐ In Progress"
            else:
                status = "✗ Unwatched"

            # Build user list with progress
            user_progress = item.get('user_progress', {})
            if user_progress:
                user_list = []
                for user in sorted(user_progress.keys()):
                    progress = user_progress[user]
                    if progress >= 80:
                        user_list.append(f"{user} (100%)")
                    elif progress > 0:
                        user_list.append(f"{user} ({int(progress)}%)")
                    else:
                        user_list.append(f"{user} (0%)")
                users = ', '.join(user_list)
            else:
                users = '-'

            last_watched = item['last_watched'].strftime('%Y-%m-%d') if item['last_watched'] else '-'

            f.write(f"| {title} | {size} | {added} | {status} | {users} | {last_watched} |\n")

        f.write("\n")

    def generate_html_report(self, categories: Dict, stats: Dict):
        """
        Generate HTML report file

        Args:
            categories: Categorized media dictionary
            stats: Category statistics dictionary
        """
        os.makedirs(self.output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(self.output_dir, f'plex_purge_report_{timestamp}.html')

        total_items = sum(s['total_items'] for s in stats.values())
        total_size = sum(s['total_size_gb'] for s in stats.values())

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Plex Media Purge Analysis Report</title>
    <style>
        :root {{
            --bg-primary: #f5f5f5;
            --bg-secondary: white;
            --bg-tertiary: #f8f9fa;
            --bg-section: #e3f2fd;
            --text-primary: #000;
            --text-secondary: #666;
            --text-tertiary: #1976d2;
            --border-color: #e0e0e0;
            --border-color-secondary: #dee2e6;
            --hover-bg: #f8f9fa;
            --section-hover: #bbdefb;
        }}

        [data-theme="dark"] {{
            --bg-primary: #1a1a1a;
            --bg-secondary: #2d2d2d;
            --bg-tertiary: #3a3a3a;
            --bg-section: #2a4a5a;
            --text-primary: #e0e0e0;
            --text-secondary: #b0b0b0;
            --text-tertiary: #64b5f6;
            --border-color: #404040;
            --border-color-secondary: #505050;
            --hover-bg: #3a3a3a;
            --section-hover: #3a5a6a;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            transition: background-color 0.3s, color 0.3s;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
        }}
        .header-content {{
            flex: 1;
        }}
        .header h1 {{
            margin: 0 0 10px 0;
        }}
        .theme-toggle {{
            display: flex;
            gap: 5px;
            background: rgba(255,255,255,0.2);
            padding: 5px;
            border-radius: 8px;
        }}
        .theme-btn {{
            padding: 8px 16px;
            border: none;
            border-radius: 5px;
            background: transparent;
            color: white;
            cursor: pointer;
            font-size: 0.9em;
            transition: background 0.3s;
        }}
        .theme-btn:hover {{
            background: rgba(255,255,255,0.2);
        }}
        .theme-btn.active {{
            background: rgba(255,255,255,0.3);
            font-weight: bold;
        }}
        .summary {{
            background: var(--bg-secondary);
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .summary-stats {{
            display: flex;
            gap: 30px;
            margin-top: 15px;
        }}
        .stat {{
            flex: 1;
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-label {{
            color: var(--text-secondary);
            font-size: 0.9em;
        }}
        .category {{
            background: var(--bg-secondary);
            margin-bottom: 30px;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .category-header {{
            background: #667eea;
            color: white;
            padding: 20px;
            font-size: 1.3em;
            font-weight: bold;
            cursor: pointer;
            user-select: none;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background 0.3s;
        }}
        .category-header:hover {{
            background: #5568d3;
        }}
        .category-header .toggle-icon {{
            font-size: 1.2em;
            transition: transform 0.3s;
        }}
        .category-header.collapsed .toggle-icon {{
            transform: rotate(-90deg);
        }}
        .category-content {{
            max-height: 5000px;
            overflow: hidden;
            transition: max-height 0.5s ease-out;
        }}
        .category-content.collapsed {{
            max-height: 0;
        }}
        .category-stats {{
            padding: 15px 20px;
            background: var(--bg-tertiary);
            border-bottom: 1px solid var(--border-color);
        }}
        .section-header {{
            background: var(--bg-section);
            padding: 12px 20px;
            font-weight: bold;
            color: var(--text-tertiary);
            margin-top: 10px;
            cursor: pointer;
            user-select: none;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background 0.3s;
        }}
        .section-header:hover {{
            background: var(--section-hover);
        }}
        .section-header .toggle-icon {{
            font-size: 1em;
            transition: transform 0.3s;
        }}
        .section-header.collapsed .toggle-icon {{
            transform: rotate(-90deg);
        }}
        .section-content {{
            max-height: 3000px;
            overflow: hidden;
            transition: max-height 0.5s ease-out;
        }}
        .section-content.collapsed {{
            max-height: 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th {{
            background: var(--bg-tertiary);
            padding: 12px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid var(--border-color-secondary);
            position: sticky;
            top: 0;
        }}
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid var(--border-color);
        }}
        tr:hover {{
            background-color: var(--hover-bg);
        }}
        .watched-yes {{
            color: #28a745;
            font-weight: bold;
        }}
        .watched-in-progress {{
            color: #ffc107;
            font-weight: bold;
        }}
        .watched-no {{
            color: #dc3545;
            font-weight: bold;
        }}
        .size-column {{
            text-align: right;
            font-family: monospace;
        }}
        .date-column {{
            color: var(--text-secondary);
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: var(--text-secondary);
            font-size: 0.9em;
        }}
        .controls {{
            background: var(--bg-secondary);
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            display: flex;
            gap: 10px;
        }}
        .btn {{
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            background: #667eea;
            color: white;
            cursor: pointer;
            font-size: 0.9em;
            transition: background 0.3s;
        }}
        .btn:hover {{
            background: #5568d3;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <h1>Plex Media Purge Analysis Report</h1>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        <div class="theme-toggle">
            <button class="theme-btn" onclick="setTheme('light')" id="theme-light">Light</button>
            <button class="theme-btn" onclick="setTheme('dark')" id="theme-dark">Dark</button>
            <button class="theme-btn active" onclick="setTheme('system')" id="theme-system">System</button>
        </div>
    </div>

    <div class="summary">
        <h2>Summary</h2>
        <div class="summary-stats">
            <div class="stat">
                <div class="stat-value">{total_items}</div>
                <div class="stat-label">Total Items</div>
            </div>
            <div class="stat">
                <div class="stat-value">{total_size:.2f} GB</div>
                <div class="stat-label">Total Size</div>
            </div>
        </div>
    </div>

    <div class="controls">
        <button class="btn" onclick="expandAll()">▼ Expand All</button>
        <button class="btn" onclick="collapseAll()">▶ Collapse All</button>
    </div>
"""

        # Add categories
        for cat_key in ['cat1_5years', 'cat2_3years', 'cat3_1year', 'cat4_large_movies', 'cat5_large_shows']:
            cat_data = categories[cat_key]
            cat_stats = stats[cat_key]

            if cat_stats['total_items'] > 0:
                html_content += self._generate_html_category(cat_key, cat_data, cat_stats)

        html_content += """
    <div class="footer">
        <p>Plex Media Purge Helper Tool</p>
    </div>

    <script>
        // Theme management
        function setTheme(theme) {{
            localStorage.setItem('theme', theme);
            applyTheme(theme);
            updateThemeButtons(theme);
        }}

        function applyTheme(theme) {{
            if (theme === 'system') {{
                const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
            }} else {{
                document.documentElement.setAttribute('data-theme', theme);
            }}
        }}

        function updateThemeButtons(activeTheme) {{
            document.querySelectorAll('.theme-btn').forEach(btn => {{
                btn.classList.remove('active');
            }});
            document.getElementById(`theme-${{activeTheme}}`).classList.add('active');
        }}

        function initTheme() {{
            const savedTheme = localStorage.getItem('theme') || 'system';
            applyTheme(savedTheme);
            updateThemeButtons(savedTheme);

            // Listen for system theme changes
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {{
                const currentTheme = localStorage.getItem('theme') || 'system';
                if (currentTheme === 'system') {{
                    applyTheme('system');
                }}
            }});
        }}

        // Toggle category visibility
        function toggleCategory(header) {{
            const content = header.nextElementSibling;
            header.classList.toggle('collapsed');
            content.classList.toggle('collapsed');
        }}

        // Toggle section visibility
        function toggleSection(header) {{
            const content = header.nextElementSibling;
            header.classList.toggle('collapsed');
            content.classList.toggle('collapsed');
        }}

        // Expand all categories and sections
        function expandAll() {{
            document.querySelectorAll('.category-header.collapsed').forEach(header => {{
                header.classList.remove('collapsed');
                header.nextElementSibling.classList.remove('collapsed');
            }});
            document.querySelectorAll('.section-header.collapsed').forEach(header => {{
                header.classList.remove('collapsed');
                header.nextElementSibling.classList.remove('collapsed');
            }});
        }}

        // Collapse all categories and sections
        function collapseAll() {{
            document.querySelectorAll('.category-header:not(.collapsed)').forEach(header => {{
                header.classList.add('collapsed');
                header.nextElementSibling.classList.add('collapsed');
            }});
            document.querySelectorAll('.section-header:not(.collapsed)').forEach(header => {{
                header.classList.add('collapsed');
                header.nextElementSibling.classList.add('collapsed');
            }});
        }}

        // Add event listeners to all category headers
        document.addEventListener('DOMContentLoaded', function() {{
            // Initialize theme
            initTheme();

            const categoryHeaders = document.querySelectorAll('.category-header');
            categoryHeaders.forEach(header => {{
                header.addEventListener('click', () => toggleCategory(header));
            }});

            const sectionHeaders = document.querySelectorAll('.section-header');
            sectionHeaders.forEach(header => {{
                header.addEventListener('click', () => toggleSection(header));
            }});
        }});
    </script>
</body>
</html>
"""

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)

        self.console.print(f"[green]HTML report saved to: {filename}[/green]")

    def _generate_html_category(self, cat_key: str, cat_data: Dict, cat_stats: Dict) -> str:
        """
        Generate HTML for a category

        Args:
            cat_key: Category key
            cat_data: Category media data
            cat_stats: Category statistics

        Returns:
            HTML string for the category
        """
        category_name = self.CATEGORY_NAMES[cat_key]

        html = f"""
    <div class="category">
        <div class="category-header">
            <span>{category_name}</span>
            <span class="toggle-icon">▼</span>
        </div>
        <div class="category-content">
            <div class="category-stats">
                <strong>Total:</strong> {cat_stats['total_items']} items, {cat_stats['total_size_gb']:.2f} GB
            </div>
"""

        # Movies
        if cat_data['movies']:
            html += f"""
            <div class="section-header">
                <span>MOVIES ({len(cat_data['movies'])} items)</span>
                <span class="toggle-icon">▼</span>
            </div>
            <div class="section-content">
                {self._generate_html_table(cat_data['movies'])}
            </div>
"""

        # TV Shows
        if cat_data['shows']:
            html += f"""
            <div class="section-header">
                <span>TV SHOWS ({len(cat_data['shows'])} items)</span>
                <span class="toggle-icon">▼</span>
            </div>
            <div class="section-content">
                {self._generate_html_table(cat_data['shows'])}
            </div>
"""

        html += """        </div>
    </div>
"""
        return html

    def _generate_html_table(self, items: List[Dict]) -> str:
        """
        Generate HTML table for media items

        Args:
            items: List of media items

        Returns:
            HTML table string
        """
        html = """
        <table>
            <thead>
                <tr>
                    <th>Title</th>
                    <th style="text-align: right;">Size</th>
                    <th>Added</th>
                    <th style="text-align: center;">Status</th>
                    <th>Watched By (Progress)</th>
                    <th>Last Watched</th>
                </tr>
            </thead>
            <tbody>
"""

        for item in items:
            # Build title with links
            title = item['title']
            if item.get('year'):
                title = f"{title} ({item['year']})"

            # Create Plex link (title becomes clickable)
            plex_url = self._get_plex_web_url(str(item['rating_key']), item['type'])
            if plex_url:
                title = f'<a href="{plex_url}" target="_blank" style="color: #667eea; text-decoration: none;">{title}</a>'

            # Add Tautulli link with icon
            tautulli_url = self._get_tautulli_url(str(item['rating_key']))
            if tautulli_url:
                title = f'{title} <a href="{tautulli_url}" target="_blank" style="color: #764ba2; text-decoration: none; font-size: 0.85em;" title="View in Tautulli">(T)</a>'

            # Add Sonarr link for TV shows
            if item['type'] == 'show' and item.get('tvdb_id'):
                sonarr_url = self._get_sonarr_url(item['tvdb_id'])
                if sonarr_url:
                    title = f'{title} <a href="{sonarr_url}" target="_blank" style="color: #4CAF50; text-decoration: none; font-size: 0.85em;" title="View in Sonarr">(S)</a>'

            # Add Radarr link for movies
            if item['type'] == 'movie' and (item.get('tmdb_id') or item.get('imdb_id')):
                radarr_url = self._get_radarr_url(item.get('tmdb_id'), item.get('imdb_id'))
                if radarr_url:
                    title = f'{title} <a href="{radarr_url}" target="_blank" style="color: #FF9800; text-decoration: none; font-size: 0.85em;" title="View in Radarr">(R)</a>'

            size = f"{item['size_gb']:.2f} GB"
            added = item['added_at'].strftime('%Y-%m-%d') if item['added_at'] else 'N/A'

            # Watch status with color coding
            watch_status = item.get('watch_status', 'unwatched')
            if watch_status == 'watched':
                status_class = "watched-yes"
                status = "✓ Watched"
            elif watch_status == 'in_progress':
                status_class = "watched-in-progress"
                status = "◐ In Progress"
            else:
                status_class = "watched-no"
                status = "✗ Unwatched"

            # Build user list with progress
            user_progress = item.get('user_progress', {})
            if user_progress:
                user_list = []
                for user in sorted(user_progress.keys()):
                    progress = user_progress[user]
                    if progress >= 80:
                        user_list.append(f"{user} (100%)")
                    elif progress > 0:
                        user_list.append(f"{user} ({int(progress)}%)")
                    else:
                        user_list.append(f"{user} (0%)")
                users = ', '.join(user_list)
            else:
                users = '-'

            last_watched = item['last_watched'].strftime('%Y-%m-%d') if item['last_watched'] else '-'

            html += f"""
                <tr>
                    <td>{title}</td>
                    <td class="size-column">{size}</td>
                    <td class="date-column">{added}</td>
                    <td style="text-align: center;" class="{status_class}">{status}</td>
                    <td>{users}</td>
                    <td class="date-column">{last_watched}</td>
                </tr>
"""

        html += """
            </tbody>
        </table>
"""
        return html
