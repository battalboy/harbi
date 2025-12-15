#!/usr/bin/env python3
"""
Roobet Team Name Collector (HTML Scraper Version)

Scrapes team names directly from the Roobet soccer page HTML.
Alternative to API-based collection.

Note: This may not work if the page is heavily JavaScript-rendered.
If most content loads via JS, use the API version instead.

Runs every 60-120 seconds (random interval).
Output: roobet_names.txt (one team name per line, sorted, no duplicates)
"""

import requests
import time
import random
import signal
import sys
import re
from typing import Set
from datetime import datetime
from bs4 import BeautifulSoup


# Configuration
OUTPUT_FILE = 'roobet_names.txt'
MIN_INTERVAL = 60  # seconds
MAX_INTERVAL = 120  # seconds
PAGE_URL = 'https://roobet.com/sports/soccer-1'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Cache-Control': 'max-age=0'
}


def load_existing_teams() -> Set[str]:
    """Load existing team names from file."""
    try:
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            teams = set(line.strip() for line in f if line.strip())
        print(f"📂 Loaded {len(teams)} existing team names from {OUTPUT_FILE}")
        return teams
    except FileNotFoundError:
        print(f"📝 Creating new file: {OUTPUT_FILE}")
        return set()


def save_teams(teams: Set[str]):
    """Save team names to file (sorted, one per line)."""
    sorted_teams = sorted(teams)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for team in sorted_teams:
            f.write(team + '\n')


def extract_team_names_from_html(html_content: str) -> Set[str]:
    """
    Extract team names from HTML content.
    
    This function tries multiple strategies:
    1. Look for JSON-LD structured data
    2. Parse HTML elements that might contain team names
    3. Look for patterns in script tags (if data is embedded)
    """
    teams = set()
    
    if not html_content:
        return teams
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Strategy 1: Look for JSON in script tags (common in modern SPAs)
        # Many sites embed initial state/data in script tags
        script_tags = soup.find_all('script')
        for script in script_tags:
            if script.string:
                # Look for team name patterns in embedded JSON
                # Common patterns: "name":"Team Name", "team":"Team Name", "competitor":"Team Name"
                name_matches = re.findall(r'"(?:name|team|competitor)"\s*:\s*"([^"]+)"', script.string)
                for match in name_matches:
                    # Filter out obvious non-team names
                    if len(match) > 2 and not match.startswith('http'):
                        teams.add(match)
        
        # Strategy 2: Look for common HTML structures
        # Classes/IDs that might contain team names (adjust based on actual HTML structure)
        selectors = [
            'div[class*="team"]',
            'span[class*="team"]',
            'div[class*="competitor"]',
            'span[class*="competitor"]',
            'div[class*="participant"]',
            'span[class*="participant"]',
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for elem in elements:
                text = elem.get_text(strip=True)
                if text and len(text) > 2:
                    teams.add(text)
        
        # Strategy 3: Look for JSON-LD structured data
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                import json
                data = json.loads(script.string)
                # Look for team/competitor info in structured data
                if isinstance(data, dict):
                    # Common keys in sports structured data
                    for key in ['competitor', 'team', 'homeTeam', 'awayTeam', 'participant']:
                        if key in data:
                            item = data[key]
                            if isinstance(item, dict) and 'name' in item:
                                teams.add(item['name'])
                            elif isinstance(item, str):
                                teams.add(item)
            except:
                pass
        
    except Exception as e:
        print(f"⚠ Error parsing HTML: {e}")
    
    return teams


def fetch_page_content() -> str:
    """Fetch the HTML content of the Roobet soccer page."""
    try:
        response = requests.get(PAGE_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"⚠ Error fetching page: {e}")
        return None


def fetch_team_names() -> Set[str]:
    """Fetch team names by scraping the HTML page."""
    html_content = fetch_page_content()
    
    if html_content:
        teams = extract_team_names_from_html(html_content)
        return teams
    
    return set()


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\n\n🛑 Stopping collection...")
    print(f"✅ Team names saved to {OUTPUT_FILE}")
    sys.exit(0)


def main():
    """Main collection loop."""
    # Check if BeautifulSoup is available
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("❌ Error: BeautifulSoup4 is not installed.")
        print("   Please install it with: pip install beautifulsoup4")
        sys.exit(1)
    
    # Register Ctrl+C handler
    signal.signal(signal.SIGINT, signal_handler)
    
    print("=" * 60, flush=True)
    print("🎰 Roobet Team Name Collector (HTML Scraper)", flush=True)
    print("=" * 60, flush=True)
    print(f"📝 Output file: {OUTPUT_FILE}", flush=True)
    print(f"⏱️  Interval: {MIN_INTERVAL}-{MAX_INTERVAL} seconds (random)", flush=True)
    print(f"🌐 URL: {PAGE_URL}", flush=True)
    print(f"⚠️  NOTE: This scraper may not work if the page is JavaScript-rendered", flush=True)
    print(f"   If you get no teams, use collect_roobet_teams.py (API version) instead", flush=True)
    print(f"🛑 Press Ctrl+C to stop\n", flush=True)
    
    # Load existing teams
    all_teams = load_existing_teams()
    initial_count = len(all_teams)
    
    fetch_count = 0
    
    try:
        while True:
            fetch_count += 1
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"[{timestamp}] Fetch #{fetch_count}...", end=" ", flush=True)
            
            # Fetch team names
            new_teams = fetch_team_names()
            
            if new_teams:
                # Find truly new teams
                before_count = len(all_teams)
                all_teams.update(new_teams)
                after_count = len(all_teams)
                new_count = after_count - before_count
                
                # Save to file
                save_teams(all_teams)
                
                # Report
                print(f"✓ Found {len(new_teams)} teams", end="")
                if new_count > 0:
                    print(f" ({new_count} NEW!)", end="")
                print(f" | Database: {len(all_teams)} unique teams")
                
                if new_count > 0:
                    # Show new teams (up to 10)
                    actually_new = sorted([t for t in new_teams if t not in (all_teams - new_teams)])[:10]
                    
                    for team in actually_new[:10]:
                        print(f"      + {team}")
                    if new_count > 10:
                        print(f"      ... and {new_count - 10} more")
            else:
                print("⚠ No teams found (page may be JavaScript-rendered)")
                print("   Consider using collect_roobet_teams.py (API version) instead")
            
            # Random wait interval
            wait_time = random.randint(MIN_INTERVAL, MAX_INTERVAL)
            print(f"   💤 Waiting {wait_time}s until next fetch...\n")
            time.sleep(wait_time)
    
    except KeyboardInterrupt:
        signal_handler(None, None)


if __name__ == '__main__':
    main()

