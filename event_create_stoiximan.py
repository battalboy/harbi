"""
Stoiximan Complete API Parser with Timestamps
Extracts soccer match data WITH 1X2 odds and timestamps from Stoiximan JSON API
Fetches BOTH live matches AND upcoming matches for comprehensive coverage
"""

import json
import sys
import cloudscraper
import requests  # Keep for exception handling
import platform
from datetime import datetime, timezone
from error_handler import handle_request_error, success_response, is_ban_indicator


# Configuration
SITE_NAME = 'Stoiximan'
OUTPUT_FILE = 'stoiximan-formatted.txt'
ERROR_LOG_FILE = 'stoiximan-error.json'

# All 181 specific league IDs for comprehensive coverage (2.7x better than region IDs)
ALL_LEAGUE_IDS = "1,2,4,5,215,216,217,218,527,1630,1635,1636,1647,1672,1673,1697,1698,10000,10008,10016,10017,10067,10210,10215,10346,10392,10467,10486,10815,11962,11963,15285,16765,16816,16823,16842,16849,16872,16880,16882,16884,16887,16888,16893,16894,16896,16901,16905,16918,16921,16932,16940,16941,16946,16947,16952,16954,16955,17024,17026,17041,17067,17069,17073,17078,17079,17080,17083,17087,17088,17093,17103,17108,17113,17118,17122,17123,17126,17158,17160,17166,17223,17246,17264,17313,17315,17370,17377,17383,17385,17405,17407,17412,17427,17439,17491,17496,17524,17530,17572,17611,17714,17727,17766,17788,17796,17802,17816,17837,17839,17877,17901,17906,17917,18092,18369,18443,181553,181647,181734,181739,181792,181811,181988,182086,182181,182215,183321,183456,184596,184721,184866,185364,186905,186962,187246,187259,187416,187589,187668,188482,188880,189547,190848,190985,191713,191910,191912,192991,192992,193121,193969,193989,194429,194430,195435,195785,195867,196183,196214,197272,197335,197549,197789,198734,201034,201720,202042,203472,203500,203860,203862,204604,205799,432g,433g,434g,435g,436g,474g,493g"

def format_timestamp_iso(unix_timestamp_ms: int) -> str:
    """
    Convert Unix timestamp (in MILLISECONDS) to ISO 8601 format.
    Stoiximan uses milliseconds. Output matches oddswar/roobet format.
    
    Args:
        unix_timestamp_ms: Unix timestamp in milliseconds (e.g., 1768770000000)
    
    Returns:
        str: ISO 8601 string (e.g., "2026-01-17T17:45:00.000Z")
    """
    try:
        dt = datetime.fromtimestamp(unix_timestamp_ms / 1000, tz=timezone.utc)
        return dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    except (ValueError, OSError):
        return "N/A"


def get_proxy_config():
    """
    Get proxy configuration based on platform.
    Uses Greece VPN proxy on Linux (remote server), direct connection on macOS.
    
    Returns:
        dict or None: Proxy configuration
    """
    if platform.system() == 'Linux':
        return {
            'http': 'http://127.0.0.1:8888',
            'https': 'http://127.0.0.1:8888'
        }
    return None


def fetch_live_matches():
    """
    Fetch live match data from Stoiximan API.
    
    Returns:
        dict: JSON response with events, markets, selections
    """
    api_url = 'https://en.stoiximan.gr/danae-webapi/api/live/overview/latest'
    params = {
        'includeVirtuals': 'false',
        'queryLanguageId': '1',
        'queryOperatorId': '2'
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json'
    }
    
    proxies = get_proxy_config()
    
    print(f"Fetching {SITE_NAME} LIVE matches...", flush=True)
    scraper = cloudscraper.create_scraper()
    response = scraper.get(api_url, params=params, headers=headers, timeout=30, proxies=proxies)
    response.raise_for_status()
    
    return response.json()


def fetch_upcoming_matches():
    """
    Fetch upcoming (prematch) matches from Stoiximan API.
    Uses ALL 181 specific league IDs for maximum coverage (2.7x better than region IDs).
    
    Returns:
        list: List of upcoming match events (already parsed)
    """
    api_url = 'https://en.stoiximan.gr/api/league/hot/upcoming'
    params = {
        'leagueId': ALL_LEAGUE_IDS,
        'req': 's,stnf,c,mb'
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:147.0) Gecko/20100101 Firefox/147.0',
        'Accept': 'application/json, text/plain, */*',
        'Referer': 'https://en.stoiximan.gr/sport/soccer/'
    }
    
    proxies = get_proxy_config()
    
    print(f"Fetching {SITE_NAME} UPCOMING matches (181 league IDs)...", flush=True)
    scraper = cloudscraper.create_scraper()
    response = scraper.get(api_url, params=params, headers=headers, timeout=30, proxies=proxies)
    response.raise_for_status()
    
    data = response.json()
    events = data.get('data', {}).get('events', [])
    
    return events


def parse_live_matches(json_data):
    """
    Parse LIVE matches with full odds data from Stoiximan live API.
    
    Args:
        json_data: JSON data from live API endpoint (includes top-level leagues dict)
        
    Returns:
        list: List of dictionaries containing match data with odds
    """
    matches = []
    
    # Extract events, markets, selections, and leagues from the JSON
    events = json_data.get('events', {})
    markets_data = json_data.get('markets', {})
    selections_data = json_data.get('selections', {})
    leagues = json_data.get('leagues', {})
    
    for event_id, event in events.items():
        try:
            # Filter for soccer only
            if event.get('sportId') != 'FOOT':
                continue
            
            # Get start time (Unix ms) and convert to ISO 8601
            start_time_ms = event.get('startTime', 0)
            start_time = format_timestamp_iso(start_time_ms) if start_time_ms else 'N/A'
            
            # Get league name from top-level leagues dict
            league_id = event.get('leagueId')
            league_info = leagues.get(str(league_id), {}) if league_id else {}
            league = league_info.get('name', 'N/A')
            
            # Get participants (teams)
            participants = event.get('participants', [])
            if len(participants) < 2:
                continue
            
            team1_name = participants[0].get('name', 'Unknown')
            team2_name = participants[1].get('name', 'Unknown')
            
            # Skip esports matches
            if '(Esports)' in team1_name or '(Esports)' in team2_name or \
               '(esports)' in team1_name or '(esports)' in team2_name:
                continue
            
            # Find 1X2 odds using marketIdList and selectionIdList
            team1_odds = 'N/A'
            draw_odds = 'N/A'
            team2_odds = 'N/A'
            
            # Get market IDs for this event
            market_ids = event.get('marketIdList', [])
            for market_id in market_ids:
                market_id_str = str(market_id)
                if market_id_str not in markets_data:
                    continue
                
                market = markets_data[market_id_str]
                market_name = market.get('name', '')
                
                # Look for Match Result market
                if market_name == 'Match Result':
                    selection_ids = market.get('selectionIdList', [])
                    
                    # Match Result typically has 3 selections: Team1, Draw, Team2
                    for sel_id in selection_ids:
                        sel_id_str = str(sel_id)
                        if sel_id_str not in selections_data:
                            continue
                        
                        sel = selections_data[sel_id_str]
                        sel_name = sel.get('name', '').lower()
                        price = sel.get('price', 'N/A')
                        
                        # Map selection to team or draw
                        if 'draw' in sel_name or sel_name == 'x':
                            draw_odds = price
                        elif team1_name.lower() in sel_name:
                            team1_odds = price
                        elif team2_name.lower() in sel_name:
                            team2_odds = price
                        else:
                            # If we can't determine, assign in order (1, X, 2)
                            if team1_odds == 'N/A':
                                team1_odds = price
                            elif draw_odds == 'N/A':
                                draw_odds = price
                            elif team2_odds == 'N/A':
                                team2_odds = price
                    
                    # Found the Match Result market, no need to check others
                    break
            
            # Build match URL
            event_url = event.get('url', '')
            match_url = f"https://en.stoiximan.gr{event_url}" if event_url else "N/A"
            
            match = {
                'team1': team1_name,
                'team2': team2_name,
                'team1_odds': team1_odds,
                'draw_odds': draw_odds,
                'team2_odds': team2_odds,
                'url': match_url,
                'start_time': start_time,
                'status': 'Canlı Maç',
                'league': league,
                'is_live': True
            }
            
            matches.append(match)
            
        except Exception as e:
            print(f"Error parsing live event {event_id}: {e}", flush=True)
            continue
    
    return matches


def parse_upcoming_matches(events):
    """
    Parse UPCOMING matches from Stoiximan upcoming API.
    
    Args:
        events: List of event objects from upcoming API
        
    Returns:
        list: List of dictionaries containing match data with odds
    """
    matches = []
    
    for event in events:
        try:
            # Filter for soccer only
            if event.get('sportId') != 'FOOT':
                continue
            
            # Get start time (Unix ms) and convert to ISO 8601
            start_time_ms = event.get('startTime', 0)
            start_time = format_timestamp_iso(start_time_ms) if start_time_ms else 'N/A'
            
            # Get league name (directly on event in upcoming API)
            league = event.get('leagueName', 'N/A')
            
            # Get participants (teams)
            participants = event.get('participants', [])
            if len(participants) < 2:
                continue
            
            team1_name = participants[0].get('name', 'Unknown')
            team2_name = participants[1].get('name', 'Unknown')
            
            # Skip esports matches
            if '(Esports)' in team1_name or '(Esports)' in team2_name or \
               '(esports)' in team1_name or '(esports)' in team2_name:
                continue
            
            # Find 1X2 odds from markets
            team1_odds = None
            draw_odds = None
            team2_odds = None
            
            markets = event.get('markets', [])
            for market in markets:
                # Look for Match Result market
                if market.get('type') == 'MRES' or market.get('name') == 'Match Result':
                    selections = market.get('selections', [])
                    for selection in selections:
                        name = selection.get('name', '')
                        price = selection.get('price')
                        
                        if name == '1':
                            team1_odds = price
                        elif name == 'X':
                            draw_odds = price
                        elif name == '2':
                            team2_odds = price
                    break
            
            # Build match URL
            event_url = event.get('url', '')
            match_url = f"https://en.stoiximan.gr{event_url}" if event_url else "N/A"
            
            match = {
                'team1': team1_name,
                'team2': team2_name,
                'team1_odds': team1_odds if team1_odds else 'N/A',
                'draw_odds': draw_odds if draw_odds else 'N/A',
                'team2_odds': team2_odds if team2_odds else 'N/A',
                'url': match_url,
                'start_time': start_time,
                'status': 'Gelen Maç',
                'league': league,
                'is_live': False
            }
            
            matches.append(match)
            
        except Exception as e:
            print(f"Error parsing upcoming event: {e}", flush=True)
            continue
    
    return matches


def format_match(match):
    """
    Format a match dictionary into the standard output format.
    Includes Status, League, and Start Time (aligned with oddswar/roobet).
    
    Args:
        match: Dictionary containing match data
        
    Returns:
        str: Formatted match string
    """
    team1 = match.get('team1', 'N/A')
    team2 = match.get('team2', 'N/A')
    team1_odds = match.get('team1_odds', 'N/A')
    draw_odds = match.get('draw_odds', 'N/A')
    team2_odds = match.get('team2_odds', 'N/A')
    link_url = match.get('url', 'N/A')
    status = match.get('status', 'Gelen Maç')
    league = match.get('league', 'N/A')
    start_time = match.get('start_time', 'N/A')
    
    return (
        f"Team 1: {team1} | Team 2: {team2} | "
        f"Team 1 Win: {team1_odds} | Draw: {draw_odds} | Team 2 Win: {team2_odds} | "
        f"Link: {link_url} | Status: {status} | League: {league} | Start Time: {start_time}"
    )


def save_formatted_matches(matches, output_file=OUTPUT_FILE):
    """
    Save formatted matches to a text file.
    File is overwritten each time to ensure only latest data.
    
    Args:
        matches: List of match dictionaries
        output_file: Output filename
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        for match in matches:
            f.write(format_match(match) + '\n')
    
    print(f"\n✅ Saved {len(matches)} matches to {output_file}")


def main():
    """Main execution function with comprehensive error handling."""
    try:
        print(f"Fetching {SITE_NAME} soccer matches (live + upcoming)...")
        print("="*60)
        
        all_matches = []
        
        # Step 1: Fetch LIVE matches
        print("\n1. Fetching LIVE matches...")
        try:
            live_data = fetch_live_matches()
            live_matches = parse_live_matches(live_data)
            all_matches.extend(live_matches)
            print(f"   Found {len(live_matches)} live matches")
        except Exception as e:
            print(f"   Error fetching live matches: {e}")
        
        # Step 2: Fetch UPCOMING matches
        print("\n2. Fetching UPCOMING matches...")
        try:
            upcoming_events = fetch_upcoming_matches()
            upcoming_matches = parse_upcoming_matches(upcoming_events)
            all_matches.extend(upcoming_matches)
            print(f"   Found {len(upcoming_matches)} upcoming matches")
        except Exception as e:
            print(f"   Error fetching upcoming matches: {e}")
        
        # Step 3: Report statistics
        print(f"\n3. Processing results...")
        matches_with_odds = [m for m in all_matches if m['team1_odds'] != 'N/A']
        live_count = sum(1 for m in all_matches if m.get('is_live', False))
        upcoming_count = len(all_matches) - live_count
        
        print(f"   Total matches: {len(all_matches)}")
        print(f"   - Live: {live_count}")
        print(f"   - Upcoming: {upcoming_count}")
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
            
            print("\n✨ Done!")
            return success_info
        else:
            print("\n⚠️  No matches found!")
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

