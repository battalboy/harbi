# Harbi

A Python-based soccer betting odds parser and web application for extracting and displaying match data from betting sites.

## Features

- 🎯 HTML parser for Stoiximan betting site
- 📊 Extracts team names and betting odds (1, X, 2)
- 🔄 Formatted output for easy data processing
- 🔐 SSL/TLS certificate configuration
- 🐍 Python 3.11 with virtual environment

## Project Structure

```
harbi/
├── stoiximan.py              # Main HTML parser
├── stoiximan.txt             # Sample HTML input
├── stoiximan-formatted.txt   # Parsed output
├── ssl_setup.py              # SSL configuration utility
├── setup_ssl_env.sh          # SSL environment setup script
├── requirements.txt          # Python dependencies
└── README.md                 # This file
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

## Usage

### Parse Stoiximan HTML

```bash
# Basic usage
python stoiximan.py stoiximan.txt

# Specify output file
python stoiximan.py stoiximan.txt output.txt
```

### Use as Python Module

```python
from stoiximan import parse_matches, format_match

# Parse HTML file
matches = parse_matches('stoiximan.txt')

# Access match data
for match in matches:
    print(f"{match['team1']} vs {match['team2']}")
    print(f"Odds: {match['team1_odds']} / {match['draw_odds']} / {match['team2_odds']}")
```

## Dependencies

- **streamlit** - Web application framework
- **pandas** - Data manipulation
- **playwright** - Browser automation
- **requests** - HTTP library
- **watchdog** - File system monitoring
- **certifi** - SSL certificates
- **rapidfuzz** - Fuzzy string matching
- **beautifulsoup4** - HTML parsing
- **lxml** - XML/HTML parser

## Development

### SSL Configuration

Set up SSL certificates for HTTPS requests:

```bash
# Set environment variables
source setup_ssl_env.sh

# Or test SSL connection
python ssl_setup.py
```

### Virtual Environment

Always activate the virtual environment before working:

```bash
source venv/bin/activate
```

## Deployment

### Ubuntu/Linux Server

The codebase is fully compatible with Ubuntu deployment. See deployment notes for:
- System dependencies
- Playwright browser setup
- Systemd service configuration
- Docker containerization

## Future Features

- 🌐 Web interface with Streamlit
- 🔄 Auto-refresh functionality
- 📡 Real-time data updates
- 📊 Data visualization
- 🗄️ Database integration

## License

All rights reserved.

## Author

Harbi Development Team

