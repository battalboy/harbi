# Harbi

A Python-based soccer betting odds parser for extracting live match data and odds from multiple betting sites.

## Features

- 🎯 Dual parser support: Stoiximan & Oddswar
- 📊 Extracts team names and 1X2 betting odds (Team 1, Draw, Team 2)
- 🚀 Single-command execution for both sites
- 🔄 Formatted output for easy data processing and comparison
- ⚡ Real-time API data fetching
- 🚫 Automatic esports filtering (Stoiximan)
- 🔗 Match links included in output
- 🐍 Python 3.11 with virtual environment

## Project Structure

```
harbi/
├── fetch_odds.sh                        # 🚀 Main script - Run both parsers
├── stoiximan_api_complete_parser.py     # Stoiximan API parser
├── oddswar_api_complete_parser.py       # Oddswar API parser
├── stoiximan-formatted.txt              # Stoiximan output (live matches)
├── oddswar-formatted.txt                # Oddswar output (live matches)
├── requirements.txt                     # Python dependencies
├── USAGE.md                             # Quick start guide
└── README.md                            # This file
```

## Installation

### Prerequisites

- Python 3.11
- pip

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd harbi
```

2. Create and activate virtual environment:
```bash
python3.11 -m venv venv
source venv/bin/activate  # On macOS/Linux
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Playwright browsers (if needed):
```bash
playwright install
```

5. Make the fetch script executable:
```bash
chmod +x fetch_odds.sh
```

## Usage

### Quick Start (Recommended) 🚀

From the project directory, fetch live odds from both Stoiximan and Oddswar with a single command:

```bash
cd harbi  # Navigate to project directory
./fetch_odds.sh
```

**That's it!** The script will:
1. 🔵 Fetch latest Stoiximan live soccer matches (esports filtered out)
2. 🟠 Fetch latest Oddswar live soccer matches  
3. 📊 Display match counts
4. ✅ Create two formatted output files

### Output Files

Both parsers create identically formatted output:

- **`stoiximan-formatted.txt`** - Stoiximan matches (no esports)
- **`oddswar-formatted.txt`** - Oddswar matches

**Format:**
```
Team 1: [name] | Team 2: [name] | Team 1 Win: [odds] | Draw: [odds] | Team 2 Win: [odds] | Link: [url]
```

**Example:**
```
Team 1: Iraq U23 | Team 2: United Arab Emirates U23 | Team 1 Win: 1.9 | Draw: 3.0 | Team 2 Win: 4.0 | Link: https://en.stoiximan.gr/live/iraq-u23-united-arab-emirates-u23/77536380/
```

### Run Individual Parsers

**Stoiximan only:**
```bash
curl -s 'https://en.stoiximan.gr/danae-webapi/api/live/overview/latest?includeVirtuals=false&queryLanguageId=1&queryOperatorId=2' \
  -H 'User-Agent: Mozilla/5.0' -H 'Accept: application/json' > stoiximan-api.json
python stoiximan_api_complete_parser.py stoiximan-api.json stoiximan-formatted.txt
```

**Oddswar only:**
```bash
python oddswar_api_complete_parser.py
```

## Dependencies

- **requests** - HTTP library for API calls
- **beautifulsoup4** - HTML parsing
- **lxml** - XML/HTML parser
- **playwright** - Browser automation
- **streamlit** - Web application framework (for future features)
- **pandas** - Data manipulation (for future features)
- **watchdog** - File system monitoring (for future features)
- **certifi** - SSL certificates
- **rapidfuzz** - Fuzzy string matching (for future features)

See `requirements.txt` for complete list.

## Development

### Virtual Environment

Always activate the virtual environment before working:

```bash
source venv/bin/activate
```

### How It Works

**Stoiximan:**
1. Fetches JSON from Stoiximan's live API endpoint
2. Parses events, markets, and selections
3. Extracts 1X2 odds from "Match Result" markets
4. Filters out esports matches
5. Formats output with match links

**Oddswar:**
1. Fetches market list from Oddswar's exchange API
2. Gets detailed odds from marketDetails endpoint
3. Extracts BACK odds only (pink boxes in UI)
4. Maps runner names to team positions
5. Formats output with match links

Both parsers output identical format for easy comparison.

## Notes

- **Stoiximan**: Geoblocked outside Greece - requires VPN connected to Greek IP address
  - If fetch fails, check that VPN is connected to Greece
- **Oddswar**: More reliable, fetches directly from API (no geoblocking)
- **Output files**: Always overwritten with fresh data on each run
- **Esports**: Automatically filtered out from Stoiximan results
- **Odds**: Stoiximan shows decimal odds, Oddswar shows BACK odds (not LAY)

## Future Features

- 📊 Odds comparison between sites
- 📈 Historical odds tracking
- 🔔 Alert system for odds changes
- 🗄️ Database storage
- 🌐 Web interface for visualization

## License

All rights reserved.

## Author

Harbi Development Team

