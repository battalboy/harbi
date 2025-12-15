#!/usr/bin/env python3
"""
Tumbet Team Names Collector

Continuously fetches Tumbet top prematch matches and collects unique team names.
Since Tumbet only provides "top" prematch games (limited set at any given time),
we need to collect over time as different matches become "top".

Runs every 60-120 seconds (random interval).
Output: tumbet_names.txt (one team name per line, sorted, no duplicates)

Note: Requires Turkish IP address for access.
"""

import requests
import json
import time
import random
import signal
import sys
from typing import Set
from datetime import datetime
from pathlib import Path

# Configuration
BASE_URL = "https://analytics-sp.googleserv.tech"
BRAND_ID = "161"  # Tumbet's brand ID
LANGUAGE = "ot"   # Turkish
OUTPUT_FILE = Path(__file__).parent / "tumbet_names.txt"
MIN_INTERVAL = 60  # seconds
MAX_INTERVAL = 120  # seconds


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\n\n🛑 Stopping collection...")
    print(f"✅ Teams saved to: {OUTPUT_FILE}")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


def load_existing_teams() -> Set[str]:
    """Load existing team names from file."""
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            teams = set(line.strip() for line in f if line.strip())
        print(f"📂 Loaded {len(teams)} existing team names from {OUTPUT_FILE}", flush=True)
        return teams
    print(f"📝 Creating new file: {OUTPUT_FILE}", flush=True)
    return set()


def save_teams(teams: Set[str]):
    """Save team names to file (sorted)."""
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for team in sorted(teams):
            f.write(f"{team}\n")


def fetch_json(url):
    """Fetch JSON data from URL."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # The response is a JSON string, so we need to parse it twice
        data_str = response.json()
        if isinstance(data_str, str):
            return json.loads(data_str)
        return data_str
    except Exception as e:
        return None


def get_top_prematch_games():
    """Get top prematch games with game IDs."""
    url = f"{BASE_URL}/api/prematch/getprematchtopgames/{LANGUAGE}"
    data = fetch_json(url)
    
    if not data:
        return []
    
    game_ids = []
    for sport in data:
        if sport.get('id') == 1 and 'gms' in sport:  # Soccer = 1
            game_ids.extend(sport['gms'])
    
    return game_ids


def get_game_details(game_ids):
    """Get detailed game information including team names."""
    if not game_ids:
        return set()
    
    # Format game IDs for API (comma-separated with leading comma)
    games_param = "," + ",".join(map(str, game_ids))
    
    url = f"{BASE_URL}/api/prematch/getprematchgameall/{LANGUAGE}/{BRAND_ID}/?games={games_param}"
    data = fetch_json(url)
    
    if not data or 'teams' not in data:
        return set()
    
    teams_data = data['teams']
    if isinstance(teams_data, str):
        teams_data = json.loads(teams_data)
    
    team_names = set()
    for team in teams_data:
        if team.get('Sport') == 1:  # Soccer only
            name = team.get('Name', '').strip()
            if name:
                team_names.add(name)
    
    return team_names


def fetch_team_names() -> Set[str]:
    """Fetch current team names from Tumbet top prematch games."""
    # Step 1: Get top prematch game IDs
    game_ids = get_top_prematch_games()
    
    if not game_ids:
        return set()
    
    # Step 2: Get team names from game details
    team_names = get_game_details(game_ids)
    
    return team_names


def main():
    print("=" * 60, flush=True)
    print("🎲 Tumbet Team Name Collector (SportWide API)", flush=True)
    print("=" * 60, flush=True)
    print(f"📝 Output file: {OUTPUT_FILE}", flush=True)
    print(f"⏱️  Interval: {MIN_INTERVAL}-{MAX_INTERVAL} seconds (random)", flush=True)
    print(f"📡 API: SportWide (analytics-sp.googleserv.tech)", flush=True)
    print(f"⚡ Fetches TOP prematch matches only", flush=True)
    print(f"⚠️  Only collects from TOP games (builds up over time)", flush=True)
    print(f"🇹🇷 Requires Turkish IP address", flush=True)
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
            
            # Fetch team names from top prematch games
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
                print(f"✓ Found {len(new_teams)} teams in top games", end="", flush=True)
                if new_count > 0:
                    print(f" ({new_count} NEW!)", end="", flush=True)
                print(f" | Database: {len(all_teams)} unique teams", flush=True)
                
                if new_count > 0:
                    # Show new teams (up to 10)
                    new_list = sorted(all_teams - (all_teams - new_teams))
                    actually_new = [t for t in new_list if t in new_teams][-new_count:]
                    
                    for team in actually_new[:10]:
                        print(f"      + {team}")
                    if new_count > 10:
                        print(f"      ... and {new_count - 10} more")
            else:
                print("⚠ No data received (check Turkish IP/VPN)", flush=True)
            
            # Random wait interval
            wait_time = random.randint(MIN_INTERVAL, MAX_INTERVAL)
            print(f"   💤 Waiting {wait_time}s until next fetch...\n", flush=True)
            time.sleep(wait_time)
    
    except KeyboardInterrupt:
        signal_handler(None, None)


if __name__ == "__main__":
    main()
