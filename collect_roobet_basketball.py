#!/usr/bin/env python3
"""
Roobet Basketball Team Name Collector

Continuously fetches Roobet LIVE and PREMATCH basketball matches and collects unique team names.
Uses the Betsby API (sptpub.com) with a two-step process:
1. Get version/timestamp from manifest endpoint
2. Use that version to fetch actual event data

Runs every 60-120 seconds (random interval).
Output: roobet_basketball_names.txt (one team name per line, sorted, no duplicates)
"""

import requests
import time
import random
import signal
import sys
import re
from typing import Set
from datetime import datetime


# Configuration
OUTPUT_FILE = 'roobet_basketball_names.txt'
MIN_INTERVAL = 60  # seconds
MAX_INTERVAL = 120  # seconds
BRAND_ID = '2186449803775455232'
BASE_URL = 'https://api-g-c7818b61-607.sptpub.com'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Origin': 'https://roobet.com',
    'Referer': 'https://roobet.com/sports'
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
    - rest_events_versions (THIS IS KEY - gives us comprehensive coverage!)
    
    Args:
        endpoint_type: 'live' or 'prematch'
    
    Returns:
        Combined dict with all events, or None on error
    """
    try:
        # Step 1: Get version manifest
        manifest_url = f"{BASE_URL}/api/v4/{endpoint_type}/brand/{BRAND_ID}/en/0"
        response = requests.get(manifest_url, headers=HEADERS, timeout=10)
        
        # Check for server errors
        if response.status_code != 200:
            print(f"\n\n❌ SERVER ERROR ({endpoint_type}) - Received HTTP {response.status_code}")
            print(f"URL: {response.url}")
            print(f"Response Headers: {dict(response.headers)}")
            print(f"Response Body (first 500 chars):\n{response.text[:500]}")
            print("\n💡 Possible causes:")
            print("   - VPN/IP blocked by Roobet")
            print("   - API endpoint changed")
            print("   - Betsby API down")
            print("\n🛑 Exiting due to server error...")
            sys.exit(1)
        
        manifest = response.json()
        
        # Get all versions to fetch
        main_version = manifest.get('version')
        if not main_version:
            print(f"\n\n❌ INVALID RESPONSE ({endpoint_type}) - No 'version' field in manifest")
            print(f"Manifest: {str(manifest)[:500]}")
            print("\n🛑 Exiting due to invalid response...")
            sys.exit(1)
        
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
            
            if response.status_code != 200:
                print(f"\n\n❌ SERVER ERROR fetching version {version} - HTTP {response.status_code}")
                print(f"URL: {response.url}")
                print(f"Response: {response.text[:500]}")
                print("\n🛑 Exiting due to server error...")
                sys.exit(1)
            
            data = response.json()
            # Merge events from this version
            if 'events' in data:
                combined_events.update(data['events'])
        
        if combined_events:
            return {'events': combined_events}
        
        # No events found at all
        print(f"\n\n⚠️  WARNING: No events found in {endpoint_type} data")
        print(f"   Manifest had {len(unique_versions)} versions but no events")
        return None
        
    except requests.RequestException as e:
        print(f"\n\n❌ NETWORK ERROR ({endpoint_type}): {e}")
        print(f"URL: {manifest_url if 'manifest_url' in locals() else 'N/A'}")
        print("\n🛑 Exiting due to network error...")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ UNEXPECTED ERROR ({endpoint_type}): {e}")
        import traceback
        traceback.print_exc()
        print("\n🛑 Exiting due to unexpected error...")
        sys.exit(1)


def is_valid_team_name(name: str) -> bool:
    """
    Filter out metadata/non-team entries.
    
    Returns False for:
    - League/season identifiers (e.g., "BBL 2025/26")
    - Metadata words (e.g., "Awards")
    - Entries with year patterns like "2024/25" or "2025/26"
    - Esports teams (e.g., "Boston Celtics (E)", "FC Barcelona (E)")
    """
    if not name or not name.strip():
        return False
    
    name_lower = name.lower()
    
    # Filter out esports teams (marked with (E))
    if '(e)' in name_lower or name.endswith(' (E)'):
        return False
    
    # Filter out common metadata words
    metadata_keywords = ['awards', 'winner', 'championship', 'tournament']
    for keyword in metadata_keywords:
        if name_lower == keyword:
            return False
    
    # Filter out year patterns (e.g., "2024/25", "2025/26")
    if re.search(r'\d{4}/\d{2}', name):
        return False
    
    # Filter out entries that are just league codes/identifiers
    # (typically all caps with numbers, less than 6 chars)
    if len(name) < 6 and name.isupper() and any(c.isdigit() for c in name):
        return False
    
    return True


def extract_team_names_from_data(data):
    """Extract team names from Betsby API response (basketball only)."""
    teams = set()
    
    if not data or not isinstance(data, dict):
        return teams
    
    # Betsby API structure: events[event_id]['desc']['competitors']
    if 'events' in data and isinstance(data['events'], dict):
        for event_id, event in data['events'].items():
            desc = event.get('desc', {})
            
            # Filter for basketball only (sport_id = '2')
            if desc.get('sport') != '2':
                continue
            
            # Get competitors from desc
            if 'competitors' in desc and isinstance(desc['competitors'], list):
                for competitor in desc['competitors']:
                    name = competitor.get('name', '')
                    if name and is_valid_team_name(name):
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
    
    print("=" * 60)
    print("🏀 Roobet Basketball Team Name Collector (LIVE + PREMATCH)")
    print("=" * 60)
    print(f"📝 Output file: {OUTPUT_FILE}")
    print(f"⏱️  Interval: {MIN_INTERVAL}-{MAX_INTERVAL} seconds (random)")
    print(f"📍 Fetches LIVE basketball matches")
    print(f"🔮 Fetches PREMATCH basketball matches (comprehensive)")
    print(f"🚫 Filters out esports teams (E), metadata, and year patterns")
    print(f"🛑 Press Ctrl+C to stop\n")
    
    # Load existing teams
    all_teams = load_existing_teams()
    initial_count = len(all_teams)
    
    fetch_count = 0
    
    try:
        while True:
            fetch_count += 1
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"[{timestamp}] Fetch #{fetch_count}...")
            
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
