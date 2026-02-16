#!/usr/bin/env python3
"""
Stoiximan Team Name Collector

Continuously fetches Stoiximan LIVE matches and collects unique team names.
Since Stoiximan only provides live events (no "all matches" endpoint),
we need to collect over time as different matches go live.

Runs every 60-120 seconds (random interval).
Output: stoiximan_names.txt (one team name per line, sorted, no duplicates)

Note: Requires VPN connected to Greek IP address.
"""

import cloudscraper
import time
import random
import signal
import sys
import platform
from typing import Set
from datetime import datetime


# Configuration
OUTPUT_FILE = 'stoiximan_names.txt'
TARGET_TEAM_COUNT = 1205  # Reference for progress percentage (Oddswar team count)
MIN_INTERVAL = 60  # seconds
MAX_INTERVAL = 120  # seconds
API_URL = 'https://en.stoiximan.gr/danae-webapi/api/live/overview/latest'
API_PARAMS = {
    'includeVirtuals': 'false',
    'queryLanguageId': '1',
    'queryOperatorId': '2'
}
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Accept': 'application/json'
}

# Proxy configuration (only used on Linux remote server)
def get_proxies():
    """Return proxy configuration if on Linux (remote server), None if macOS (local)."""
    if platform.system() == 'Linux':
        # Remote server - use Gluetun Greece proxy
        return {
            'http': 'http://127.0.0.1:8888',
            'https': 'http://127.0.0.1:8888'
        }
    else:
        # macOS - using system-wide ExpressVPN
        return None


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


def fetch_team_names() -> Set[str]:
    """Fetch current team names from Stoiximan live API."""
    try:
        proxies = get_proxies()
        # Use cloudscraper to bypass Cloudflare protection
        scraper = cloudscraper.create_scraper()
        response = scraper.get(API_URL, params=API_PARAMS, headers=HEADERS, proxies=proxies, timeout=30)
        
        # Check for server errors
        if response.status_code != 200:
            print(f"\n\n❌ SERVER ERROR - Received HTTP {response.status_code}")
            print(f"URL: {response.url}")
            print(f"Response Headers: {dict(response.headers)}")
            print(f"Response Body (first 500 chars):\n{response.text[:500]}")
            print("\n💡 Possible causes:")
            print("   - VPN not connected to Greek IP")
            print("   - Cloudflare blocking")
            print("   - API endpoint changed")
            print("\n🛑 Exiting due to server error...")
            sys.exit(1)
        
        data = response.json()
        
        # Check if we got valid data
        if not data or 'events' not in data:
            print(f"\n\n❌ INVALID RESPONSE - No data or missing 'events' field")
            print(f"Response: {str(data)[:500]}")
            print("\n🛑 Exiting due to invalid response...")
            sys.exit(1)
        
        teams = set()
        events = data.get('events', {})
        
        # Only get soccer events
        for event_id, event in events.items():
            if event.get('sportId') != 'FOOT':
                continue
            
            participants = event.get('participants', [])
            if len(participants) < 2:
                continue
            
            team1 = participants[0].get('name', '')
            team2 = participants[1].get('name', '')
            
            # Skip esports matches
            if '(Esports)' in team1 or '(Esports)' in team2 or \
               '(esports)' in team1 or '(esports)' in team2:
                continue
            
            if team1:
                teams.add(team1)
            if team2:
                teams.add(team2)
        
        return teams
    
    except Exception as e:
        print(f"\n\n❌ NETWORK ERROR: {e}")
        print(f"URL: {API_URL}")
        print("\n💡 Check VPN connection to Greece or Cloudflare protection")
        print("\n🛑 Exiting due to network error...")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("\n🛑 Exiting due to unexpected error...")
        sys.exit(1)


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\n\n🛑 Stopping collection...")
    print(f"✅ Team names saved to {OUTPUT_FILE}")
    sys.exit(0)


def main():
    """Main collection loop."""
    # Register Ctrl+C handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Detect environment
    proxies = get_proxies()
    env_info = "🔌 Using Gluetun proxy (127.0.0.1:8888)" if proxies else "🌐 Using system-wide VPN"
    
    print("=" * 60)
    print("🔵 Stoiximan Team Name Collector (LIVE MATCHES)")
    print("=" * 60)
    print(f"📝 Output file: {OUTPUT_FILE}")
    print(f"📊 Reference: {TARGET_TEAM_COUNT} teams (Oddswar count)")
    print(f"⏱️  Interval: {MIN_INTERVAL}-{MAX_INTERVAL} seconds (random)")
    print(f"🇬🇷 Requires VPN connected to Greek IP")
    print(f"{env_info}")
    print(f"⚠️  Only collects from LIVE matches (builds up over time)")
    print(f"🚫 Esports automatically filtered out")
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
            
            # Fetch team names from live matches
            new_teams = fetch_team_names()
            
            if new_teams:
                # Find truly new teams BEFORE merging
                truly_new_teams = new_teams - all_teams
                
                # Merge with existing teams
                all_teams.update(new_teams)
                
                # Save to file
                save_teams(all_teams)
                
                # Report
                progress = (len(all_teams) / TARGET_TEAM_COUNT) * 100
                print(f"✓ Found {len(new_teams)} teams in live matches", end="")
                if truly_new_teams:
                    print(f" ({len(truly_new_teams)} NEW!)", end="")
                print(f" | Database: {len(all_teams)}/{TARGET_TEAM_COUNT} ({progress:.1f}%)")
                
                if truly_new_teams:
                    # Show new teams (up to 10)
                    for team in sorted(truly_new_teams)[:10]:
                        print(f"      + {team}")
                    if len(truly_new_teams) > 10:
                        print(f"      ... and {len(truly_new_teams) - 10} more")
            else:
                print("⚠ No data received (check VPN)")
            
            # Random wait interval
            wait_time = random.randint(MIN_INTERVAL, MAX_INTERVAL)
            print(f"   💤 Waiting {wait_time}s until next fetch...\n")
            time.sleep(wait_time)
    
    except KeyboardInterrupt:
        signal_handler(None, None)


if __name__ == '__main__':
    main()

