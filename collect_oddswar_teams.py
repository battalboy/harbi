#!/usr/bin/env python3
"""
Oddswar Team Name Collector

Fetches ALL available soccer matches from Oddswar (all pages, interval=all)
and collects unique team names. Runs every 60-120 seconds (random interval).
Output: oddswar_names.txt (one team name per line, sorted, no duplicates)
"""

import requests
import time
import random
import signal
import sys
from typing import Set
from datetime import datetime


# Configuration
OUTPUT_FILE = 'oddswar_names.txt'
MIN_INTERVAL = 60  # seconds
MAX_INTERVAL = 120  # seconds
API_URL = 'https://www.oddswar.com/api/brand/1oddswar/exchange/soccer-1'
BASE_PARAMS = {
    'marketTypeId': 'MATCH_ODDS',
    'interval': 'all',  # Get all matches, not just live
    'size': '50',
    'setCache': 'false'
}
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/json'
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


def fetch_all_team_names() -> Set[str]:
    """Fetch ALL team names from Oddswar API (paginated)."""
    all_teams = set()
    
    try:
        # First, get page 0 to find total pages
        params = BASE_PARAMS.copy()
        params['page'] = '0'
        
        response = requests.get(API_URL, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        last_page = data.get('lastPage', 0)
        total_pages = last_page + 1
        
        print(f"   📄 Found {total_pages} pages to fetch", end=" ")
        
        # Fetch all pages
        for page in range(0, total_pages):
            params['page'] = str(page)
            
            response = requests.get(API_URL, params=params, headers=HEADERS, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            markets = data.get('exchangeMarkets', [])
            
            # Extract teams from this page
            for market in markets:
                event = market.get('event', {})
                event_name = event.get('name', '')
                
                # Parse "Team1 v Team2" format
                if ' v ' in event_name:
                    parts = event_name.split(' v ')
                    if len(parts) == 2:
                        all_teams.add(parts[0].strip())
                        all_teams.add(parts[1].strip())
            
            # Small delay between pages
            if page < total_pages - 1:
                time.sleep(0.1)
        
        print(f"(fetched {total_pages} pages)")
        return all_teams
    
    except requests.RequestException as e:
        print(f"❌ Error fetching data: {e}")
        return set()
    except Exception as e:
        print(f"❌ Error parsing data: {e}")
        return set()


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\n\n🛑 Stopping collection...")
    print(f"✅ Team names saved to {OUTPUT_FILE}")
    sys.exit(0)


def main():
    """Main collection loop."""
    # Register Ctrl+C handler
    signal.signal(signal.SIGINT, signal_handler)
    
    print("=" * 60)
    print("🟠 Oddswar Team Name Collector (ALL MATCHES)")
    print("=" * 60)
    print(f"📝 Output file: {OUTPUT_FILE}")
    print(f"⏱️  Interval: {MIN_INTERVAL}-{MAX_INTERVAL} seconds (random)")
    print(f"🌍 Fetches ALL available matches (not just live)")
    print(f"🛑 Press Ctrl+C to stop\n")
    
    # Load existing teams
    all_teams = load_existing_teams()
    initial_count = len(all_teams)
    
    fetch_count = 0
    
    try:
        while True:
            fetch_count += 1
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"[{timestamp}] Fetch #{fetch_count}...", end=" ")
            
            # Fetch ALL team names (all pages)
            new_teams = fetch_all_team_names()
            
            if new_teams:
                # Find truly new teams
                before_count = len(all_teams)
                all_teams.update(new_teams)
                after_count = len(all_teams)
                new_count = after_count - before_count
                
                # Save to file
                save_teams(all_teams)
                
                # Report
                print(f"   ✓ Found {len(new_teams)} total teams", end="")
                if new_count > 0:
                    print(f" ({new_count} NEW!)", end="")
                print(f" | Database: {len(all_teams)} unique teams")
                
                if new_count > 0:
                    # Show new teams (limit to 10)
                    newly_added = sorted([t for t in new_teams if t not in (all_teams - new_teams)])[:10]
                    for team in newly_added:
                        print(f"      + {team}")
                    if new_count > 10:
                        print(f"      ... and {new_count - 10} more")
            else:
                print("   ⚠ No data received")
            
            # Random wait interval
            wait_time = random.randint(MIN_INTERVAL, MAX_INTERVAL)
            print(f"   💤 Waiting {wait_time}s until next fetch...\n")
            time.sleep(wait_time)
    
    except KeyboardInterrupt:
        signal_handler(None, None)


if __name__ == '__main__':
    main()
