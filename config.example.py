"""
Configuration Example for Plex Media Purge Helper Tool

Copy this file to 'config.py' and fill in your actual credentials and preferences.

DO NOT commit config.py to version control - it contains your API keys!
"""

import os

# ============================================================================
# PLEX SERVER CONFIGURATION
# ============================================================================

# Plex server URL (usually http://localhost:32400 for local servers)
PLEX_URL = os.getenv('PLEX_URL', 'http://localhost:32400')

# Plex authentication token
# Get from: Plex Settings > Account > View XML and look for X-Plex-Token
# Or from: https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/
PLEX_TOKEN = os.getenv('PLEX_TOKEN', 'YOUR_PLEX_TOKEN_HERE')


# ============================================================================
# TAUTULLI CONFIGURATION
# ============================================================================

# Tautulli server URL (usually http://localhost:8181)
TAUTULLI_URL = os.getenv('TAUTULLI_URL', 'http://localhost:8181')

# Tautulli API key
# Get from: Tautulli Settings > Web Interface > API > API Key
TAUTULLI_API_KEY = os.getenv('TAUTULLI_API_KEY', 'YOUR_TAUTULLI_API_KEY_HERE')


# ============================================================================
# SONARR CONFIGURATION
# ============================================================================

# Sonarr server URL (usually http://localhost:8989)
SONARR_URL = os.getenv('SONARR_URL', 'http://localhost:8989')

# Sonarr API key
# Get from: Sonarr Settings > General > Security > API Key
SONARR_API_KEY = os.getenv('SONARR_API_KEY', 'YOUR_SONARR_API_KEY_HERE')

# Enable/disable Sonarr integration (adds (S) links to TV shows in reports)
SONARR_ENABLED = True


# ============================================================================
# RADARR CONFIGURATION
# ============================================================================

# Radarr server URL (usually http://localhost:7878)
RADARR_URL = os.getenv('RADARR_URL', 'http://localhost:7878')

# Radarr API key
# Get from: Radarr Settings > General > Security > API Key
RADARR_API_KEY = os.getenv('RADARR_API_KEY', 'YOUR_RADARR_API_KEY_HERE')

# Enable/disable Radarr integration (adds (R) links to movies in reports)
RADARR_ENABLED = True


# ============================================================================
# LIBRARY EXCLUSIONS
# ============================================================================

# List of library names to exclude from scanning
# Use the exact names as they appear in Plex
EXCLUDED_LIBRARIES = [
    # Example libraries you might want to exclude:
    # 'Home Videos',
    # 'Music',
    # 'Audiobooks',
    # 'Family Photos',
]


# ============================================================================
# CATEGORIZATION THRESHOLDS
# ============================================================================

THRESHOLDS = {
    # Age thresholds (in days)
    'old_5years': 1825,      # 5 years = 1825 days
    'old_3years': 1095,      # 3 years = 1095 days
    'old_1year': 365,        # 1 year = 365 days

    # Size thresholds (in GB)
    'large_movie': 30,       # Movies larger than 30 GB
    'large_series': 100,     # TV series larger than 100 GB
}


# ============================================================================
# OUTPUT CONFIGURATION
# ============================================================================

# Default output format
# Options: 'terminal', 'markdown', 'html', 'all'
OUTPUT_FORMAT = 'terminal'

# Directory for saving markdown and HTML reports
OUTPUT_DIR = 'output'


# ============================================================================
# DISPLAY CONFIGURATION
# ============================================================================

# Show progress bars during scanning (recommended for large libraries)
SHOW_PROGRESS = True

# Sort items by size (largest first) within each category
# If False, items will be sorted by date added (oldest first)
SORT_BY_SIZE = True


# ============================================================================
# ADVANCED SETTINGS (Optional)
# ============================================================================

# Minimum percentage watched to consider media as "watched"
# Default is 80% (used in tautulli_client.py)
# MIN_WATCH_PERCENTAGE = 80
