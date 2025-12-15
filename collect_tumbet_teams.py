#!/usr/bin/env python3
"""
Tumbet Team Names Collector
Collects soccer team names from Tumbet using the SportWide API.
"""

import requests
import json
import time
from pathlib import Path

# API Configuration
BASE_URL = "https://analytics-sp.googleserv.tech"
BRAND_ID = "161"  # Tumbet's brand ID
LANGUAGE = "ot"   # Turkish

# File paths
OUTPUT_FILE = Path(__file__).parent / "tumbet_names.txt"

def fetch_json(url):
    """Fetch JSON data from URL"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # The response is a JSON string, so we need to parse it twice
        data_str = response.json()
        if isinstance(data_str, str):
            return json.loads(data_str)
        return data_str
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def get_top_prematch_games():
    """Get top prematch games with game IDs"""
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
    """Get detailed game information including team names"""
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

def load_existing_teams():
    """Load existing teams from file"""
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_teams(teams):
    """Save teams to file (sorted)"""
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for team in sorted(teams):
            f.write(f"{team}\n")

def main():
    print("=" * 60)
    print("Tumbet Team Names Collector")
    print("=" * 60)
    
    # Load existing teams
    all_teams = load_existing_teams()
    initial_count = len(all_teams)
    print(f"\nExisting teams: {initial_count}")
    
    # Fetch top prematch games
    print("\nFetching top prematch soccer games...")
    game_ids = get_top_prematch_games()
    print(f"Found {len(game_ids)} game IDs")
    
    if not game_ids:
        print("No games found!")
        return
    
    # Fetch team details from games
    print("\nFetching team details...")
    new_teams = get_game_details(game_ids)
    
    # Merge with existing teams
    all_teams.update(new_teams)
    
    # Save to file
    save_teams(all_teams)
    
    # Report results
    new_count = len(all_teams) - initial_count
    print(f"\n{'=' * 60}")
    print(f"Results:")
    print(f"  Total teams: {len(all_teams)}")
    print(f"  New teams: {new_count}")
    print(f"  Output file: {OUTPUT_FILE}")
    print(f"{'=' * 60}\n")

if __name__ == "__main__":
    main()

