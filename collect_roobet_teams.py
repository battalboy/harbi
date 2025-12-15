#!/usr/bin/env python3
"""
Roobet Team Name Collector

Continuously fetches Roobet LIVE and PREMATCH matches and collects unique team names.
Uses the Betsby API (sptpub.com) with a two-step process:
1. Get version/timestamp from manifest endpoint
2. Use that version to fetch actual event data

Runs every 60-120 seconds (random interval).
Output: roobet_names.txt (one team name per line, sorted, no duplicates)
"""

import requests
import time
import random
import signal
import sys
from typing import Set
from datetime import datetime


# Configuration
OUTPUT_FILE = 'roobet_names.txt'
MIN_INTERVAL = 60  # seconds
MAX_INTERVAL = 120  # seconds
BRAND_ID = '2186449803775455232'
BASE_URL = 'https://api-g-c7818b61-607.sptpub.com'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Origin': 'https://roobet.com',
    'Referer': 'https://roobet.com/sports/soccer-1'
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


def fetch_events_data(endpoint_type='live'):
    """
    Fetch events data using Betsby API two-step process.
    
    For prematch, this fetches from ALL version endpoints:
    - main version
    - top_events_versions
    - rest_events_versions (THIS IS KEY - gives us 700+ teams!)
    
    Args:
        endpoint_type: 'live' or 'prematch'
    
    Returns:
        Combined dict with all events, or None
    """
    try:
        # Step 1: Get version manifest
        manifest_url = f"{BASE_URL}/api/v4/{endpoint_type}/brand/{BRAND_ID}/en/0"
        response = requests.get(manifest_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        manifest = response.json()
        
        # Get all versions to fetch
        main_version = manifest.get('version')
        if not main_version:
            return None
        
        # For prematch, also get top_events_versions and rest_events_versions
        versions_to_fetch = [main_version]
        if endpoint_type == 'prematch':
            top_versions = manifest.get('top_events_versions', [])
            rest_versions = manifest.get('rest_events_versions', [])
            versions_to_fetch.extend(top_versions)
            versions_to_fetch.extend(rest_versions)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_versions = []
        for v in versions_to_fetch:
            if v not in seen:
                seen.add(v)
                unique_versions.append(v)
        
        # Step 2: Fetch data from all versions and combine
        combined_events = {}
        
        for version in unique_versions:
            events_url = f"{BASE_URL}/api/v4/{endpoint_type}/brand/{BRAND_ID}/en/{version}"
            response = requests.get(events_url, headers=HEADERS, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # Merge events from this version
                if 'events' in data:
                    combined_events.update(data['events'])
        
        if combined_events:
            return {'events': combined_events}
        
        return None
        
    except Exception as e:
        return None


def extract_team_names_from_data(data):
    """Extract team names from Betsby API response (soccer only)."""
    teams = set()
    
    if not data or not isinstance(data, dict):
        return teams
    
    # Betsby API structure: events[event_id]['desc']['competitors']
    if 'events' in data and isinstance(data['events'], dict):
        for event_id, event in data['events'].items():
            desc = event.get('desc', {})
            
            # Filter for soccer only (sport_id = '1')
            if desc.get('sport') != '1':
                continue
            
            # Get competitors from desc
            if 'competitors' in desc and isinstance(desc['competitors'], list):
                for competitor in desc['competitors']:
                    name = competitor.get('name', '')
                    if name:
                        teams.add(name)
    
    return teams


def fetch_team_names() -> Set[str]:
    """Fetch current team names from Roobet/Betsby API."""
    teams = set()
    
    # Fetch from LIVE matches
    live_data = fetch_events_data('live')
    if live_data:
        live_teams = extract_team_names_from_data(live_data)
        teams.update(live_teams)
    
    # Fetch from PREMATCH (upcoming matches)
    prematch_data = fetch_events_data('prematch')
    if prematch_data:
        prematch_teams = extract_team_names_from_data(prematch_data)
        teams.update(prematch_teams)
    
    return teams


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\n\n🛑 Stopping collection...")
    print(f"✅ Team names saved to {OUTPUT_FILE}")
    sys.exit(0)


def main():
    """Main collection loop."""
    # Register Ctrl+C handler
    signal.signal(signal.SIGINT, signal_handler)
    
    print("=" * 60, flush=True)
    print("🎰 Roobet Team Name Collector (Betsby API)", flush=True)
    print("=" * 60, flush=True)
    print(f"📝 Output file: {OUTPUT_FILE}", flush=True)
    print(f"⏱️  Interval: {MIN_INTERVAL}-{MAX_INTERVAL} seconds (random)", flush=True)
    print(f"📡 API: Betsby (sptpub.com)", flush=True)
    print(f"⚡ Fetches BOTH live and prematch matches", flush=True)
    print(f"⚽ Soccer only (sport_id = 1)", flush=True)
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
                # Find truly new teams BEFORE merging
                truly_new_teams = new_teams - all_teams
                
                # Merge with existing teams
                all_teams.update(new_teams)
                
                # Save to file
                save_teams(all_teams)
                
                # Report
                print(f"✓ Found {len(new_teams)} teams", end="")
                if truly_new_teams:
                    print(f" ({len(truly_new_teams)} NEW!)", end="")
                print(f" | Database: {len(all_teams)} unique teams")
                
                if truly_new_teams:
                    # Show new teams (up to 10)
                    for team in sorted(truly_new_teams)[:10]:
                        print(f"      + {team}")
                    if len(truly_new_teams) > 10:
                        print(f"      ... and {len(truly_new_teams) - 10} more")
            else:
                print("⚠ No data received (API may be restricted)")
            
            # Random wait interval
            wait_time = random.randint(MIN_INTERVAL, MAX_INTERVAL)
            print(f"   💤 Waiting {wait_time}s until next fetch...\n")
            time.sleep(wait_time)
    
    except KeyboardInterrupt:
        signal_handler(None, None)


if __name__ == '__main__':
    main()

