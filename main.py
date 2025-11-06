#!/usr/bin/env python3
"""
Plex Media Purge Helper Tool

Analyzes Plex media libraries to identify content that may be candidates for purging
based on age, watch history, and file size.
"""

import sys
import os
import argparse
from rich.console import Console
from rich.panel import Panel

# Force UTF-8 encoding for stdout/stderr to handle Unicode characters
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Import configuration
try:
    import config
except ImportError:
    print("Error: config.py not found. Please create config.py with your settings.")
    print("See config.example.py for reference.")
    sys.exit(1)

# Import modules
from plex_client import PlexClient
from tautulli_client import TautulliClient
from analyzer import MediaAnalyzer
from reporter import Reporter


def main():
    """Main entry point"""
    console = Console()

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Plex Media Purge Helper - Identify media for potential removal'
    )
    parser.add_argument(
        '--format',
        choices=['terminal', 'markdown', 'html', 'all'],
        default=config.OUTPUT_FORMAT,
        help='Output format (default: terminal)'
    )
    parser.add_argument(
        '--no-progress',
        action='store_true',
        help='Disable progress indicators'
    )
    parser.add_argument(
        '--sort-by',
        choices=['size', 'date'],
        default='size' if config.SORT_BY_SIZE else 'date',
        help='Sort items by size or date added (default: size)'
    )

    args = parser.parse_args()

    # Print header
    console.print()
    console.print(Panel.fit(
        "[bold cyan]Plex Media Purge Helper Tool[/bold cyan]\n"
        "[dim]Analyzing media for potential removal[/dim]",
        border_style="cyan"
    ))
    console.print()

    # Validate configuration
    if not config.PLEX_TOKEN:
        console.print("[red]Error: PLEX_TOKEN not set in config.py[/red]")
        console.print("Get your token from Plex: Settings > Account > X-Plex-Token")
        sys.exit(1)

    if not config.TAUTULLI_API_KEY:
        console.print("[red]Error: TAUTULLI_API_KEY not set in config.py[/red]")
        console.print("Get your API key from Tautulli: Settings > Web Interface > API")
        sys.exit(1)

    # Initialize clients
    console.print("[cyan]Connecting to Plex server...[/cyan]")
    plex = PlexClient(config.PLEX_URL, config.PLEX_TOKEN)

    if not plex.connect():
        console.print("[red]Failed to connect to Plex server. Exiting.[/red]")
        sys.exit(1)

    console.print(f"[green]✓[/green] Connected to Plex server: {plex.get_server_name()}")

    console.print("[cyan]Connecting to Tautulli...[/cyan]")
    tautulli = TautulliClient(config.TAUTULLI_URL, config.TAUTULLI_API_KEY)

    if not tautulli.test_connection():
        console.print("[red]Failed to connect to Tautulli. Exiting.[/red]")
        sys.exit(1)

    console.print("[green]✓[/green] Connected to Tautulli")
    console.print()

    # Get libraries
    console.print("[cyan]Fetching libraries...[/cyan]")
    libraries = plex.get_libraries(config.EXCLUDED_LIBRARIES)

    if not libraries:
        console.print("[yellow]No libraries found or all libraries excluded.[/yellow]")
        sys.exit(0)

    console.print(f"[green]✓[/green] Found {len(libraries)} libraries to scan:")
    for lib in libraries:
        console.print(f"  - {lib['name']} ({lib['type']})")
    console.print()

    # Collect all media items
    console.print("[cyan]Collecting media items from libraries...[/cyan]")
    all_media_items = []

    for library in libraries:
        lib_name = library['name']
        console.print(f"  Scanning: {lib_name}...")
        items = plex.get_media_items(lib_name)
        all_media_items.extend(items)
        console.print(f"    Found {len(items)} items")

    console.print(f"[green]✓[/green] Total media items collected: {len(all_media_items)}")
    console.print()

    # Analyze media
    console.print("[cyan]Analyzing media items and fetching watch history...[/cyan]")
    console.print("[dim]This may take a while for large libraries...[/dim]")
    console.print()

    analyzer = MediaAnalyzer(plex, tautulli, config.THRESHOLDS)
    show_progress = config.SHOW_PROGRESS and not args.no_progress
    categories = analyzer.analyze_media(all_media_items, show_progress=show_progress)

    # Sort items if requested
    sort_by_size = args.sort_by == 'size'
    for cat_key, cat_data in categories.items():
        cat_data['movies'] = analyzer.sort_items(cat_data['movies'], by_size=sort_by_size)
        cat_data['shows'] = analyzer.sort_items(cat_data['shows'], by_size=sort_by_size)

    # Get statistics
    stats = analyzer.get_category_stats(categories)

    console.print()
    console.print("[green]✓[/green] Analysis complete!")
    console.print()

    # Generate reports
    plex_server_id = plex.get_server_id()
    reporter = Reporter(
        config.OUTPUT_DIR,
        plex_url=config.PLEX_URL,
        tautulli_url=config.TAUTULLI_URL,
        plex_server_id=plex_server_id
    )
    reporter.generate_report(categories, stats, format=args.format)

    console.print()
    console.print("[bold green]Done![/bold green]")
    console.print()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        console = Console()
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)
