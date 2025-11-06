# Plex Media Purge Helper Tool

A Python tool that analyzes your Plex Media Server libraries to identify content that may be candidates for purging based on age, watch history, and file size.

## Features

- **Multi-criteria Analysis**: Categorizes media based on:
  - Age (5 years, 3 years, 1 year)
  - File size (large movies > 30GB, large TV series > 100GB)
- **Watch History Tracking**: Shows which users have watched each item and when
- **Duplicate Prevention**: Items only appear in their highest priority category
- **Library Filtering**: Exclude specific libraries from analysis
- **Multiple Output Formats**:
  - Terminal output with rich formatting
  - Markdown reports
  - HTML reports with interactive tables
- **Separate Media Types**: Movies and TV shows are visually separated in each category

## Requirements

- Python 3.7 or higher
- Plex Media Server
- Tautulli (for detailed watch history tracking)

## Installation

### Quick Setup (Recommended)

**Windows:**
```bash
# Run the setup script
setup.bat
```

**Linux/Mac:**
```bash
# Make scripts executable
chmod +x setup.sh run.sh

# Run the setup script
./setup.sh
```

The setup script will:
- Create a Python virtual environment
- Install all dependencies
- Create config.py from the template

### Manual Setup

1. **Clone or download this repository**

2. **Create and activate a virtual environment**:

   **Windows:**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

   **Linux/Mac:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure the tool**:
   ```bash
   # Copy the example configuration
   cp config.example.py config.py

   # Edit config.py with your details
   ```

### Get API Credentials

1. **Get your API credentials**:

   **Plex Token**:
   - Go to Plex Settings → Account
   - View XML and look for `X-Plex-Token`
   - Or follow: https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/

   **Tautulli API Key**:
   - Go to Tautulli Settings → Web Interface → API
   - Copy the API Key

2. **Edit [config.py](config.py)** and add your credentials:
   ```python
   PLEX_URL = 'http://localhost:32400'
   PLEX_TOKEN = 'your-plex-token-here'

   TAUTULLI_URL = 'http://localhost:8181'
   TAUTULLI_API_KEY = 'your-tautulli-api-key-here'
   ```

## Configuration

### Basic Settings

Edit [config.py](config.py) to customize:

```python
# Exclude specific libraries
EXCLUDED_LIBRARIES = [
    'Home Videos',
    'Music',
]

# Adjust thresholds
THRESHOLDS = {
    'old_5years': 1825,      # 5 years in days
    'old_3years': 1095,      # 3 years in days
    'old_1year': 365,        # 1 year in days
    'large_movie': 30,       # GB
    'large_series': 100,     # GB
}

# Output preferences
OUTPUT_FORMAT = 'terminal'  # or 'markdown', 'html', 'all'
OUTPUT_DIR = 'output'       # Directory for reports
SORT_BY_SIZE = True         # Sort by size (or date if False)
```

## Usage

### Using the Run Scripts (Recommended)

**Windows:**
```bash
# Basic usage
run.bat

# With options
run.bat --format html
run.bat --format all --sort-by date
```

**Linux/Mac:**
```bash
# Basic usage
./run.sh

# With options
./run.sh --format html
./run.sh --format all --sort-by date
```

### Manual Usage (Virtual Environment)

If you prefer to activate the virtual environment manually:

**Windows:**
```bash
venv\Scripts\activate
python main.py
```

**Linux/Mac:**
```bash
source venv/bin/activate
python main.py
```

### Command Options

**Basic Usage:**
```bash
python main.py              # Terminal output (default)
```

**Output Formats:**
```bash
python main.py --format markdown    # Markdown report
python main.py --format html        # HTML report
python main.py --format all         # All formats
```

**Additional Options:**
```bash
python main.py --sort-by date       # Sort by date instead of size
python main.py --no-progress        # Disable progress indicators
```

**Command-Line Help:**
```bash
python main.py --help
```

## Categories

The tool categorizes media in **priority order** (items only appear once):

1. **Category 1**: Added over 5 years ago
2. **Category 2**: Added over 3 years ago
3. **Category 3**: Added over 1 year ago
4. **Category 4**: Large movies (over 30GB)
5. **Category 5**: Large TV series (over 100GB)

### For Each Item, You'll See:

- **Title** (with year) - Clickable links to Plex and Tautulli
- **File Size** (in GB)
- **Date Added**
- **Watch Status**:
  - ✓ Watched (at least one user completed 80%+)
  - ◐ In Progress (started but not completed)
  - ✗ Unwatched (never played)
- **Watched By (Progress)** - List of users with their watch progress percentage
  - Format: `Username (percent%)`
  - Shows individual progress for each user who has viewed the item
- **Last Watched** (date)

## Example Output

### Terminal Output
```
══════════════════════════════════════════════════════════════════════════════
Plex Media Purge Analysis Report
══════════════════════════════════════════════════════════════════════════════

Total Items Found: 45
Total Size: 1,234.56 GB

Category 1: Added Over 5 Years Ago
══════════════════════════════════════════════════════════════════════════════
Total: 12 items, 345.67 GB

MOVIES (8 items)
┌──────────────────────────┬──────────┬────────────┬──────────────┬────────────────────────────┬──────────────┐
│ Title                    │ Size     │ Added      │ Status       │ Watched By (Progress)      │ Last Watched │
├──────────────────────────┼──────────┼────────────┼──────────────┼────────────────────────────┼──────────────┤
│ Old Movie (2015)         │ 25.34 GB │ 2018-03-15 │ ✓ Watched    │ John (100%), Sarah (100%)  │ 2020-06-10   │
│ Partially Seen (2019)    │ 22.10 GB │ 2019-05-20 │ ◐ In Progress│ Mike (45%)                 │ 2024-01-15   │
│ Forgotten Film (2016)    │ 18.92 GB │ 2017-11-20 │ ✗ Unwatched  │ -                          │ -            │
└──────────────────────────┴──────────┴────────────┴──────────────┴────────────────────────────┴──────────────┘

TV SHOWS (4 items)
┌──────────────────────────┬──────────┬────────────┬──────────────┬────────────────────────────┬──────────────┐
│ Title                    │ Size     │ Added      │ Status       │ Watched By (Progress)      │ Last Watched │
├──────────────────────────┼──────────┼────────────┼──────────────┼────────────────────────────┼──────────────┤
│ Old Series (2014)        │ 85.73 GB │ 2019-01-10 │ ✓ Watched    │ Mike (100%), John (100%)   │ 2021-02-15   │
│ Started Show (2020)      │ 45.20 GB │ 2020-08-12 │ ◐ In Progress│ Sarah (62%)                │ 2024-11-01   │
└──────────────────────────┴──────────┴────────────┴──────────────┴────────────────────────────┴──────────────┘
```

### Markdown Output

Reports are saved to the `output/` directory with timestamps:
- `output/plex_purge_report_20250105_143022.md`

### HTML Output

Interactive HTML reports with sortable tables:
- `output/plex_purge_report_20250105_143022.html`

Open in any web browser for a clean, styled view.

## Project Structure

```
plex-purge-helper/
├── main.py              # Entry point
├── config.py            # Your configuration (DO NOT commit!)
├── config.example.py    # Configuration template
├── plex_client.py       # Plex API wrapper
├── tautulli_client.py   # Tautulli API wrapper
├── analyzer.py          # Media categorization logic
├── reporter.py          # Output generation
├── requirements.txt     # Python dependencies
├── setup.bat            # Windows setup script
├── setup.sh             # Linux/Mac setup script
├── run.bat              # Windows run script
├── run.sh               # Linux/Mac run script
├── .gitignore           # Git ignore file
├── README.md            # This file
├── venv/                # Virtual environment (created by setup)
└── output/              # Generated reports (created automatically)
```

## How It Works

1. **Connects** to your Plex server and Tautulli instance
2. **Fetches** all libraries (excluding specified ones)
3. **Collects** metadata for all movies and TV shows:
   - File sizes
   - Date added
   - Plex rating keys
4. **Queries** Tautulli for detailed watch history of each item:
   - Tracks per-user watch progress (percentage completed)
   - Determines overall watch status (Watched/In Progress/Unwatched)
   - Records which users have viewed the item
   - Captures last watched date
5. **Categorizes** items based on priority rules
6. **Generates** reports in your chosen format(s) with clickable links to Plex and Tautulli

## Watch Progress Tracking

The tool provides detailed watch progress information for every media item:

### Watch Status Categories

- **✓ Watched** - At least one user has completed 80% or more of the content
- **◐ In Progress** - Started by one or more users but not completed (< 80%)
- **✗ Unwatched** - Never played or viewed by any user

### Per-User Progress

For each user who has viewed an item, the tool shows:
- **Username** - Plex username of the viewer
- **Progress Percentage** - Highest completion percentage achieved by that user
  - 100% = Completed (watched 80%+ of content)
  - 1-79% = In progress
  - 0% = Started but minimal progress

### Why This Matters

This detailed tracking helps you make informed decisions:
- **Avoid deleting partially-watched content** - See what users are currently watching
- **Identify truly unwatched media** - Distinguish between "never started" and "in progress"
- **Understand viewing patterns** - See which users have watched what content
- **Multi-user awareness** - One user completing a show doesn't hide others' progress

### Example Scenarios

**Scenario 1:** A TV series shows as "In Progress" with "Sarah (62%)"
- Sarah has watched 62% of the series
- You may want to keep it since she's actively watching

**Scenario 2:** A movie shows as "Watched" with "John (100%), Mike (45%)"
- John completed it (watched 80%+)
- Mike started but didn't finish (45%)
- Status shows "Watched" because at least one user completed it

**Scenario 3:** An old movie shows as "Unwatched" with "-"
- No users have ever started watching it
- Strong candidate for removal

## Important Notes

### Watch History

- Tautulli only tracks data from when it was installed
- An item is considered "watched" if **at least one user** has viewed it to 80%+ completion
- **Per-user progress tracking** shows each user's highest completion percentage
- Multiple users watching the same item are all listed with individual progress
- "In Progress" status appears when users have started but not completed (< 80%) the content

### File Sizes

- For movies: Total size of all media files
- For TV shows: Combined size of ALL episodes in the series
- Sizes are calculated from Plex's media database

### Performance

- Large libraries (1000+ items) may take several minutes to analyze
- Each item requires a Tautulli API call for watch history
- Progress bars help track long-running scans

### Privacy & Security

- **Never commit [config.py](config.py)** - it contains your API tokens!
- Keep your Plex token and Tautulli API key secure
- API keys grant full access to their respective services

## Troubleshooting

### "Error: Invalid Plex token"
- Verify your `PLEX_TOKEN` in [config.py](config.py)
- Make sure you copied the entire token
- Check that your Plex server is running

### "Failed to connect to Tautulli"
- Verify `TAUTULLI_URL` and `TAUTULLI_API_KEY` in [config.py](config.py)
- Ensure Tautulli is running
- Check that the URL is accessible

### No items found
- Check that libraries aren't all in `EXCLUDED_LIBRARIES`
- Verify your Plex libraries have content
- Make sure library types are 'movie' or 'show'

### Missing watch history
- Tautulli only tracks from installation date forward
- Check that Tautulli has been running while content was watched
- Verify Tautulli is properly connected to your Plex server

## Use Cases

This tool helps you:
- Identify old content that's never been watched
- Find large files consuming disk space
- Audit your library for content to archive or remove
- Make informed decisions about what to keep/delete
- Generate reports to review with other server users

## Disclaimer

This tool **only generates reports** - it does not delete any media files. You must manually review the reports and decide what (if anything) to remove from your Plex server.

Always maintain backups of important media before deleting anything!

## License

This project is provided as-is for personal use. Feel free to modify and adapt it to your needs.

## Contributing

Suggestions and improvements are welcome! This tool was created for personal use but can be extended with additional features.

## Future Enhancements

Potential features to add:
- Direct deletion from the tool (with confirmations)
- Email reports on a schedule
- More categorization criteria
- Integration with other Plex statistics tools
- Web interface
- Database caching for faster re-runs

---

**Happy organizing!**