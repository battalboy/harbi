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

import requests
import time
import random
import signal
import sys
from typing import Set
from datetime import datetime


# Configuration
OUTPUT_FILE = 'stoiximan_names.txt'
TARGET_TEAM_COUNT = 814  # Stop when we reach Oddswar's team count
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
        response = requests.get(API_URL, params=API_PARAMS, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        
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
    
    except requests.RequestException as e:
        print(f"❌ Error fetching data: {e}")
        print(f"   💡 Check VPN connection to Greece")
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
    print("🔵 Stoiximan Team Name Collector (LIVE MATCHES)")
    print("=" * 60)
    print(f"📝 Output file: {OUTPUT_FILE}")
    print(f"🎯 Target: {TARGET_TEAM_COUNT} teams (will auto-stop)")
    print(f"⏱️  Interval: {MIN_INTERVAL}-{MAX_INTERVAL} seconds (random)")
    print(f"🇬🇷 Requires VPN connected to Greek IP")
    print(f"⚠️  Only collects from LIVE matches (builds up over time)")
    print(f"🚫 Esports automatically filtered out")
    print(f"🛑 Press Ctrl+C to stop manually\n")
    
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
                # Find truly new teams
                before_count = len(all_teams)
                all_teams.update(new_teams)
                after_count = len(all_teams)
                new_count = after_count - before_count
                
                # Save to file
                save_teams(all_teams)
                
                # Report
                progress = (len(all_teams) / TARGET_TEAM_COUNT) * 100
                print(f"✓ Found {len(new_teams)} teams in live matches", end="")
                if new_count > 0:
                    print(f" ({new_count} NEW!)", end="")
                print(f" | Database: {len(all_teams)}/{TARGET_TEAM_COUNT} ({progress:.1f}%)")
                
                if new_count > 0:
                    # Show new teams
                    newly_added = sorted([t for t in new_teams if t in all_teams and t not in (all_teams - {t} - new_teams)])[:10]
                    new_list = sorted(all_teams - (all_teams - new_teams))
                    actually_new = [t for t in new_list if t in new_teams][-new_count:]
                    
                    for team in actually_new[:10]:
                        print(f"      + {team}")
                    if new_count > 10:
                        print(f"      ... and {new_count - 10} more")
                
                # Check if we've reached target
                if len(all_teams) >= TARGET_TEAM_COUNT:
                    print(f"\n{'='*60}")
                    print(f"🎯 TARGET REACHED!")
                    print(f"{'='*60}")
                    print(f"✅ Collected {len(all_teams)} unique teams (target: {TARGET_TEAM_COUNT})")
                    print(f"✅ Matches Oddswar team count!")
                    print(f"✅ Teams saved to {OUTPUT_FILE}")
                    print(f"\n💡 You can now proceed with team matching!")
                    print(f"{'='*60}\n")
                    sys.exit(0)
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

