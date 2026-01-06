#!/usr/bin/env python3
"""
Tumbet Team Names Collector

Continuously fetches Tumbet matches from:
- LIVE matches (in-play)
- ALL prematch matches (comprehensive coverage via getheader endpoint)

Uses the comprehensive /api/sport/getheader endpoint to get ALL soccer games,
not just "top games". This provides ~1,700+ teams vs ~109 from top games only.

Collects unique team names from both sources.
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
from typing import Set, Tuple
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


def fetch_json(url, exit_on_error=True):
    """Fetch JSON data from URL with proper error handling."""
    try:
        response = requests.get(url, timeout=10)
        
        # Check for server errors
        if response.status_code != 200:
            if exit_on_error:
                print(f"\n\n❌ SERVER ERROR - Received HTTP {response.status_code}")
                print(f"URL: {response.url}")
                print(f"Response Headers: {dict(response.headers)}")
                print(f"Response Body (first 500 chars):\n{response.text[:500]}")
                print("\n💡 Possible causes:")
                print("   - Not using Turkish IP address")
                print("   - Cloudflare blocking")
                print("   - API endpoint changed")
                print("\n🛑 Exiting due to server error...")
                sys.exit(1)
            else:
                return None
        
        # The response is a JSON string, so we need to parse it twice
        data_str = response.json()
        if isinstance(data_str, str):
            return json.loads(data_str)
        return data_str
    
    except requests.RequestException as e:
        if exit_on_error:
            print(f"\n\n❌ NETWORK ERROR: {e}")
            print(f"URL: {url}")
            print("\n💡 Check Turkish IP/VPN connection")
            print("\n🛑 Exiting due to network error...")
            sys.exit(1)
        else:
            return None
    except Exception as e:
        if exit_on_error:
            print(f"\n\n❌ UNEXPECTED ERROR: {e}")
            import traceback
            traceback.print_exc()
            print("\n🛑 Exiting due to unexpected error...")
            sys.exit(1)
        else:
            return None


def get_live_games():
    """Get live games with game IDs (optional - endpoint may not exist)."""
    url = f"{BASE_URL}/api/live/getlivegames/{LANGUAGE}"
    data = fetch_json(url, exit_on_error=False)  # Don't exit if live endpoint fails
    
    if not data:
        return []
    
    game_ids = []
    for sport in data:
        if sport.get('id') == 1 and 'gms' in sport:  # Soccer = 1
            game_ids.extend(sport['gms'])
    
    return game_ids


def get_all_prematch_games():
    """Get ALL prematch games with game IDs using comprehensive getheader endpoint.
    
    This endpoint returns a hierarchical structure:
    OT → Sports → Regions → Championships → GameSmallItems
    
    Returns ~1,239 games with ~1,700+ unique teams (vs ~69 games with ~109 teams from top games).
    """
    url = f"{BASE_URL}/api/sport/getheader/{LANGUAGE}"
    data = fetch_json(url, exit_on_error=True)  # Exit if endpoint fails (critical)
    
    if not data:
        print(f"\n\n❌ INVALID RESPONSE - getheader returned empty data")
        print(f"URL: {url}")
        print("\n🛑 Exiting due to invalid response...")
        sys.exit(1)
    
    # Navigate hierarchical structure to extract all soccer game IDs
    game_ids = []
    
    if 'OT' in data:
        ot_data = data['OT']
        sports = ot_data.get('Sports', {})
        
        # Get soccer (Sport ID = 1)
        soccer = sports.get('1', {})
        if not soccer:
            print(f"\n\n❌ NO SOCCER DATA - Soccer (id=1) not found in getheader")
            print(f"Available sports: {list(sports.keys())}")
            print("\n🛑 Exiting - no soccer data available...")
            sys.exit(1)
        
        # Iterate through regions and championships to collect all game IDs
        regions = soccer.get('Regions', {})
        for region_data in regions.values():
            champs = region_data.get('Champs', {})
            for champ_data in champs.values():
                games = champ_data.get('GameSmallItems', {})
                if games:
                    game_ids.extend(games.keys())
    
    if not game_ids:
        print(f"\n\n❌ NO GAMES FOUND - getheader returned no soccer games")
        print(f"Data structure: {str(data)[:500]}")
        print("\n🛑 Exiting - no games found...")
        sys.exit(1)
    
    return game_ids


def get_game_details(game_ids, game_type='prematch'):
    """Get detailed game information including team names."""
    if not game_ids:
        return set()
    
    # Format game IDs for API (comma-separated with leading comma)
    games_param = "," + ",".join(map(str, game_ids))
    
    # Different endpoints for live vs prematch
    if game_type == 'live':
        url = f"{BASE_URL}/api/live/getlivegameall/{LANGUAGE}/{BRAND_ID}/?games={games_param}"
        exit_on_error = False  # Don't exit if live endpoint fails
    else:
        url = f"{BASE_URL}/api/prematch/getprematchgameall/{LANGUAGE}/{BRAND_ID}/?games={games_param}"
        exit_on_error = True  # Exit if prematch fails (critical)
    
    data = fetch_json(url, exit_on_error=exit_on_error)
    
    if not data or 'teams' not in data:
        if exit_on_error:
            print(f"\n\n❌ INVALID RESPONSE - game details missing 'teams' field")
            print(f"URL: {url}")
            print(f"Response: {str(data)[:500] if data else 'None'}")
            print("\n🛑 Exiting due to invalid response...")
            sys.exit(1)
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
    
    if not team_names and exit_on_error:
        print(f"\n\n❌ NO TEAMS FOUND - 'teams' field exists but no soccer teams extracted")
        print(f"Teams data structure: {str(teams_data)[:500]}")
        print("\n🛑 Exiting - no teams found...")
        sys.exit(1)
    
    return team_names


def get_game_details_batched(game_ids, game_type='prematch', batch_size=100):
    """Get game details in batches to avoid URL length limits.
    
    Args:
        game_ids: List of game IDs to fetch
        game_type: 'live' or 'prematch'
        batch_size: Number of game IDs per batch (default 100)
    
    Returns:
        Set of team names from all batches
    """
    if not game_ids:
        return set()
    
    all_teams = set()
    total_batches = (len(game_ids) + batch_size - 1) // batch_size  # Ceiling division
    
    for i in range(0, len(game_ids), batch_size):
        batch = game_ids[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        
        # Fetch teams for this batch
        batch_teams = get_game_details(batch, game_type)
        all_teams.update(batch_teams)
        
        # Show progress for large batches
        if total_batches > 1:
            print(f"      [Batch {batch_num}/{total_batches}: {len(batch)} games, {len(batch_teams)} teams]", flush=True)
    
    return all_teams


def fetch_team_names() -> Tuple[Set[str], int, int, int]:
    """Fetch current team names from Tumbet LIVE and ALL prematch games.
    
    Returns:
        tuple: (all_teams, live_count, prematch_count, total_games)
    """
    all_teams = set()
    live_count = 0
    prematch_count = 0
    total_games = 0
    
    # Step 1: Get LIVE game IDs and teams (optional)
    live_game_ids = get_live_games()
    if live_game_ids:
        live_teams = get_game_details(live_game_ids, 'live')
        all_teams.update(live_teams)
        live_count = len(live_teams)
        total_games += len(live_game_ids)
    
    # Step 2: Get ALL prematch game IDs and teams (comprehensive coverage)
    prematch_game_ids = get_all_prematch_games()
    if prematch_game_ids:
        total_games += len(prematch_game_ids)
        # Use batched fetching for large number of games
        prematch_teams = get_game_details_batched(prematch_game_ids, 'prematch', batch_size=100)
        all_teams.update(prematch_teams)
        prematch_count = len(prematch_teams)
    
    return all_teams, live_count, prematch_count, total_games


def main():
    print("=" * 60, flush=True)
    print("🎲 Tumbet Team Name Collector (SportWide API)", flush=True)
    print("=" * 60, flush=True)
    print(f"📝 Output file: {OUTPUT_FILE}", flush=True)
    print(f"⏱️  Interval: {MIN_INTERVAL}-{MAX_INTERVAL} seconds (random)", flush=True)
    print(f"📡 API: SportWide (analytics-sp.googleserv.tech)", flush=True)
    print(f"📍 Fetches LIVE matches (if available)", flush=True)
    print(f"📅 Fetches ALL prematch matches (comprehensive coverage)", flush=True)
    print(f"🚀 Uses /api/sport/getheader for ~1,700+ teams", flush=True)
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
            
            # Fetch team names from LIVE and ALL prematch games
            new_teams, live_count, prematch_count, total_games = fetch_team_names()
            
            if new_teams:
                # Find truly new teams
                before_count = len(all_teams)
                all_teams.update(new_teams)
                after_count = len(all_teams)
                new_count = after_count - before_count
                
                # Save to file
                save_teams(all_teams)
                
                # Report
                source_info = []
                if live_count > 0:
                    source_info.append(f"{live_count} live")
                if prematch_count > 0:
                    source_info.append(f"{prematch_count} prematch")
                source_str = "+".join(source_info) if source_info else "0"
                
                print(f"✓ Found {len(new_teams)} teams from {total_games} games ({source_str})", end="", flush=True)
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
