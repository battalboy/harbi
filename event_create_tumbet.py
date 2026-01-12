"""
Tumbet Complete API Parser

This script fetches live and prematch soccer matches from Tumbet's API (SportWide) and extracts:
- Team names
- Match odds (1X2 - Team 1 Win, Draw, Team 2 Win)
- Match links

Output is formatted identically to oddswar-formatted.txt, stoiximan-formatted.txt, and roobet-formatted.txt for easy comparison.
"""

import json
import requests
import os
from pathlib import Path
from typing import List, Dict, Optional
from error_handler import handle_request_error, success_response, is_ban_indicator


# Configuration
SITE_NAME = 'Tumbet'
OUTPUT_FILE = 'tumbet-formatted.txt'
ERROR_LOG_FILE = 'tumbet-error.json'
BASE_URL = "https://analytics-sp.googleserv.tech"
BRAND_ID = "161"  # Tumbet's brand ID
LANGUAGE = "ot"   # Turkish
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/json'
}


def fetch_json(url: str) -> Dict:
    """
    Fetch JSON data from URL with proper error handling.
    
    Args:
        url: API endpoint URL
    
    Returns:
        Parsed JSON data as dict
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        # The response might be double-encoded JSON
        data = response.json()
        if isinstance(data, str):
            return json.loads(data)
        return data
    
    except requests.RequestException as e:
        print(f"Error fetching from {url}: {e}")
        return {}
    except Exception as e:
        print(f"Error parsing JSON from {url}: {e}")
        return {}


def fetch_live_games() -> List[int]:
    """
    Fetch live game IDs from Tumbet API.
    
    Returns:
        List of live game IDs
    """
    url = f"{BASE_URL}/api/live/getlivegames/{LANGUAGE}"
    
    print(f"Fetching live games...", flush=True)
    data = fetch_json(url)
    
    if not data:
        print("  No live games data")
        return []
    
    game_ids = []
    for sport in data:
        if sport.get('id') == 1 and 'gms' in sport:  # Soccer = 1
            game_ids.extend(sport['gms'])
    
    print(f"  Found {len(game_ids)} live soccer games")
    return game_ids


def fetch_prematch_top_games() -> List[int]:
    """
    Fetch top prematch game IDs from Tumbet API.
    
    Returns:
        List of prematch game IDs
    """
    url = f"{BASE_URL}/api/prematch/getprematchtopgames/{LANGUAGE}"
    
    print(f"Fetching top prematch games...", flush=True)
    data = fetch_json(url)
    
    if not data:
        print("  No prematch data")
        return []
    
    game_ids = []
    for sport in data:
        if sport.get('id') == 1 and 'gms' in sport:  # Soccer = 1
            game_ids.extend(sport['gms'])
    
    print(f"  Found {len(game_ids)} top prematch soccer games")
    return game_ids


def fetch_game_details(game_ids: List[int], game_type: str = 'prematch') -> Optional[Dict]:
    """
    Fetch detailed game information including teams, odds, and match data.
    
    Args:
        game_ids: List of game IDs to fetch
        game_type: 'live' or 'prematch'
    
    Returns:
        Dict with game details or None
    """
    if not game_ids:
        return None
    
    # Format game IDs for API (comma-separated with leading comma)
    games_param = "," + ",".join(map(str, game_ids))
    
    # Different endpoints for live vs prematch
    if game_type == 'live':
        url = f"{BASE_URL}/api/live/getlivegameall/{LANGUAGE}/{BRAND_ID}/?games={games_param}"
    else:
        url = f"{BASE_URL}/api/prematch/getprematchgameall/{LANGUAGE}/{BRAND_ID}/?games={games_param}"
    
    print(f"  Fetching {game_type} game details for {len(game_ids)} games...", flush=True)
    data = fetch_json(url)
    
    if not data:
        print(f"    No data returned")
        return None
    
    return data


def extract_1x2_odds(game_ev: Dict) -> tuple:
    """
    Extract 1X2 odds from game event data.
    
    Tumbet API structure:
    game["ev"]: {
        "448": {  # Market ID 448 = 1X2
            "selection_id": {
                "pos": 1,  # Position: 1 = Home, 2 = Draw, 3 = Away
                "coef": 1.91  # Coefficient (odds)
            },
            ...
        }
    }
    
    Args:
        game_ev: Event dictionary from game data
    
    Returns:
        tuple: (team1_odds, draw_odds, team2_odds) or (None, None, None)
    """
    team1_odds = None
    draw_odds = None
    team2_odds = None
    
    if not game_ev or not isinstance(game_ev, dict):
        return team1_odds, draw_odds, team2_odds
    
    # Find 1X2 market (market ID = "448")
    market_1x2 = game_ev.get("448", {})
    
    if not market_1x2:
        return team1_odds, draw_odds, team2_odds
    
    # Extract odds from selections
    for selection_id, selection_data in market_1x2.items():
        if not isinstance(selection_data, dict):
            continue
            
        position = selection_data.get('pos')
        coefficient = selection_data.get('coef')
        
        if position == 1:  # Home win
            team1_odds = coefficient
        elif position == 2:  # Draw
            draw_odds = coefficient
        elif position == 3:  # Away win
            team2_odds = coefficient
    
    return team1_odds, draw_odds, team2_odds


def parse_game_details(data: Dict, game_type: str = 'prematch') -> List[Dict]:
    """
    Parse game details into match dictionaries.
    
    Args:
        data: Game details response from API
        game_type: 'live' or 'prematch'
    
    Returns:
        List of match dictionaries
    """
    matches = []
    
    if not data:
        return matches
    
    # Extract teams and games data
    teams_data = data.get('teams', [])
    games_data = data.get('game', [])  # Note: 'game' not 'gms'
    
    # Handle double-encoded JSON
    if isinstance(teams_data, str):
        teams_data = json.loads(teams_data)
    if isinstance(games_data, str):
        games_data = json.loads(games_data)
    
    # Create team ID -> team name mapping
    team_map = {}
    for team in teams_data:
        if team.get('Sport') == 1:  # Soccer only
            team_id = team.get('ID')  # Note: 'ID' not 'Id'
            team_name = team.get('Name', '').strip()
            if team_id and team_name:
                team_map[team_id] = team_name
    
    # Process each game
    for game in games_data:
        try:
            # Filter for soccer only
            if game.get('sport') != 1:
                continue
            
            game_id = game.get('id')
            team1_id = game.get('t1')  # Note: 't1' not 'T1Id'
            team2_id = game.get('t2')  # Note: 't2' not 'T2Id'
            
            # Get team names
            team1_name = team_map.get(team1_id, 'Unknown')
            team2_name = team_map.get(team2_id, 'Unknown')
            
            # Extract 1X2 odds from game ev (events)
            game_ev = game.get('ev', {})
            team1_odds, draw_odds, team2_odds = extract_1x2_odds(game_ev)
            
            # Build match URL (direct link to iframe content)
            # Parent page URL doesn't work because iframe uses postMessage communication
            # Direct iframe URL format: https://www.tumbet803.com/sportwide/index.html?lang=tr&brand=161&theme=default-dark-theme#/prematch?match={game_id}
            match_url = f"https://www.tumbet803.com/sportwide/index.html?lang=tr&brand=161&theme=default-dark-theme#/prematch?match={game_id}"
            
            # Get additional info
            region_id = game.get('region', '')
            start_time_unix = game.get('stunix', '')
            
            match = {
                'id': game_id,
                'team1': team1_name,
                'team2': team2_name,
                'team1_odds': team1_odds if team1_odds else 'N/A',
                'draw_odds': draw_odds if draw_odds else 'N/A',
                'team2_odds': team2_odds if team2_odds else 'N/A',
                'region_id': region_id,
                'start_time_unix': start_time_unix,
                'url': match_url,
                'is_live': game_type == 'live'
            }
            
            matches.append(match)
            
        except Exception as e:
            print(f"    Error parsing game {game.get('id', 'unknown')}: {e}")
            continue
    
    return matches


def format_match(match: Dict) -> str:
    """
    Format a match dictionary into a human-readable string.
    Format matches other formatted.txt files exactly.
    
    Args:
        match: A dictionary containing match data
    
    Returns:
        str: A formatted string representing the match
    """
    team1 = match.get('team1', 'N/A')
    team2 = match.get('team2', 'N/A')
    team1_odds = match.get('team1_odds', 'N/A')
    draw_odds = match.get('draw_odds', 'N/A')
    team2_odds = match.get('team2_odds', 'N/A')
    link_url = match.get('url', 'N/A')
    
    return (
        f"Team 1: {team1} | Team 2: {team2} | "
        f"Team 1 Win: {team1_odds} | Draw: {draw_odds} | Team 2 Win: {team2_odds} | "
        f"Link: {link_url}"
    )


def save_formatted_matches(matches: List[Dict], output_file: str = 'tumbet-formatted.txt'):
    """
    Save formatted matches to a text file.
    File is overwritten each time to ensure only latest data.
    
    Args:
        matches: List of match dictionaries
        output_file: Output filename
    """
    # Ensure the directory exists
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for match in matches:
            f.write(format_match(match) + '\n')
    
    print(f"\n✅ Saved {len(matches)} matches to {output_file}")


def main():
    """Main execution function with comprehensive error handling."""
    try:
        print(f"Fetching {SITE_NAME} live and prematch soccer matches...")
        print("=" * 60)
        
        all_matches = []
        
        # Step 1: Fetch LIVE matches
        print("\n1. Fetching LIVE matches...")
        live_game_ids = fetch_live_games()
        if live_game_ids:
            live_data = fetch_game_details(live_game_ids, 'live')
            if live_data:
                live_matches = parse_game_details(live_data, 'live')
                all_matches.extend(live_matches)
                print(f"    Parsed {len(live_matches)} live matches")
            else:
                print("    No live data received")
        else:
            print("    No live games available")
        
        # Step 2: Fetch PREMATCH matches (top games)
        print("\n2. Fetching PREMATCH (top) matches...")
        prematch_game_ids = fetch_prematch_top_games()
        if prematch_game_ids:
            prematch_data = fetch_game_details(prematch_game_ids, 'prematch')
            if prematch_data:
                prematch_matches = parse_game_details(prematch_data, 'prematch')
                all_matches.extend(prematch_matches)
                print(f"    Parsed {len(prematch_matches)} prematch matches")
            else:
                print("    No prematch data received")
        else:
            print("    No prematch games available")
        
        # Step 3: Report statistics
        print(f"\n3. Processing results...")
        matches_with_odds = [m for m in all_matches if m['team1_odds'] != 'N/A']
        print(f"   Total matches: {len(all_matches)}")
        print(f"   Matches with 1X2 odds: {len(matches_with_odds)}")
        print(f"   Matches missing odds: {len(all_matches) - len(matches_with_odds)}")
        
        # Step 4: Save to file
        if all_matches:
            print("\n4. Saving formatted output...")
            save_formatted_matches(all_matches)
            
            # Write success status
            success_info = success_response(SITE_NAME)
            with open(ERROR_LOG_FILE, 'w', encoding='utf-8') as f:
                json.dump(success_info, f, ensure_ascii=False, indent=2)
            
            # Show preview
            print("\nPreview (first 5 matches with odds):")
            print("-" * 80)
            preview_matches = [m for m in all_matches if m['team1_odds'] != 'N/A'][:5]
            for i, match in enumerate(preview_matches, 1):
                print(f"{i}. {format_match(match)}")
            
            print("\n✨ Done!")
            return success_info
        else:
            print("\n⚠️  No matches found!")
            print("\n💡 This might mean:")
            print("   - No live or prematch games currently available")
            print("   - Turkish IP/VPN required for access")
            print("   - API endpoint may have changed")
            
            # Write empty output file
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                f.write('')
            # Write NoEventsFound status
            error_info = handle_request_error(SITE_NAME, Exception("NoEventsFound"))
            with open(ERROR_LOG_FILE, 'w', encoding='utf-8') as f:
                json.dump(error_info, f, ensure_ascii=False, indent=2)
            return error_info
        
    except requests.exceptions.HTTPError as e:
        # HTTP error with status code
        status_code = e.response.status_code if (e.response is not None) else None
        error_info = handle_request_error(SITE_NAME, e, status_code)
        
        print(f"\n❌ HTTP Error {status_code}: {error_info['error_message']}")
        
        # Check for ban indicators
        if is_ban_indicator(error_info['error_type'], status_code):
            print(f"\n⚠️  WARNING: Possible IP ban detected for {SITE_NAME}!")
            print(f"   Consider stopping all requests and waiting before retrying.")
        
        # Write error log and empty output
        with open(ERROR_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(error_info, f, ensure_ascii=False, indent=2)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write('')
        
        return error_info
        
    except requests.exceptions.ConnectionError as e:
        error_info = handle_request_error(SITE_NAME, e)
        print(f"\n❌ Connection Error: {error_info['error_message']}")
        
        with open(ERROR_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(error_info, f, ensure_ascii=False, indent=2)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write('')
        
        return error_info
        
    except requests.exceptions.Timeout as e:
        error_info = handle_request_error(SITE_NAME, e)
        print(f"\n❌ Timeout Error: {error_info['error_message']}")
        
        with open(ERROR_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(error_info, f, ensure_ascii=False, indent=2)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write('')
        
        return error_info
        
    except json.JSONDecodeError as e:
        error_info = handle_request_error(SITE_NAME, e)
        print(f"\n❌ JSON Parse Error: {error_info['error_message']}")
        
        with open(ERROR_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(error_info, f, ensure_ascii=False, indent=2)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write('')
        
        return error_info
        
    except Exception as e:
        error_info = handle_request_error(SITE_NAME, e)
        print(f"\n❌ Unexpected Error: {error_info['error_message']}")
        print(f"   Technical details: {str(e)}")
        
        with open(ERROR_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(error_info, f, ensure_ascii=False, indent=2)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write('')
        
        return error_info


if __name__ == '__main__':
    result = main()
    # Exit with error code if there was an error
    if result and result.get('error', False):
        exit(1)
    else:
        exit(0)

