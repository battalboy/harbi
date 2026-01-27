"""
Stoiximan Basketball Complete API Parser with Timestamps
Extracts basketball match data WITH 2-way odds and timestamps from Stoiximan JSON API
Fetches from featured basketball leagues (Euroleague, NBA, Greek Cup, Champions League)
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
OUTPUT_FILE = 'stoiximan-basketball-formatted.txt'
ERROR_LOG_FILE = 'stoiximan-basketball-error.json'

# Basketball league IDs (discovered via browser investigation)
BASKETBALL_LEAGUE_IDS = ['439g', '441g', '446g', '456g']  # Euroleague, NBA, Greek Cup, Champions League

# Turkish month names for timestamp formatting
TURKISH_MONTHS = [
    'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
    'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'
]


def format_timestamp_turkish(unix_timestamp_ms: int) -> str:
    """
    Convert Unix timestamp (in MILLISECONDS) to Turkish format.
    Stoiximan uses milliseconds, not seconds!
    
    Args:
        unix_timestamp_ms: Unix timestamp in milliseconds (e.g., 1768770000000)
    
    Returns:
        str: Turkish formatted timestamp (e.g., "17 Ocak 2026 saat 17:45 UTC")
    """
    try:
        # Convert milliseconds to seconds, then to datetime (UTC)
        dt = datetime.fromtimestamp(unix_timestamp_ms / 1000, tz=timezone.utc)
        
        # Format: "17 Ocak 2026 saat 17:45 UTC"
        day = dt.day
        month = TURKISH_MONTHS[dt.month - 1]
        year = dt.year
        hour = dt.hour
        minute = dt.minute
        
        return f"{day} {month} {year} saat {hour:02d}:{minute:02d} UTC"
    except Exception as e:
        # If conversion fails, return N/A
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
    Fetch live basketball match data from Stoiximan API.
    
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
    
    print(f"Fetching {SITE_NAME} LIVE basketball matches...", flush=True)
    scraper = cloudscraper.create_scraper()
    response = scraper.get(api_url, params=params, headers=headers, timeout=30, proxies=proxies)
    response.raise_for_status()
    
    return response.json()


def fetch_league_matches(league_id: str):
    """
    Fetch matches for a specific basketball league from Stoiximan API.
    
    Args:
        league_id: Basketball league ID (e.g., '439g' for Euroleague)
    
    Returns:
        list: List of event objects from the API
    """
    api_url = f'https://en.stoiximan.gr/api/sports/BASK/hot/trending/leagues/{league_id}/events'
    params = {
        'req': 'la,s,stnf,c,mb'
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:147.0) Gecko/20100101 Firefox/147.0',
        'Accept': 'application/json, text/plain, */*',
        'Referer': 'https://en.stoiximan.gr/sport/basketball/'
    }
    
    proxies = get_proxy_config()
    
    scraper = cloudscraper.create_scraper()
    response = scraper.get(api_url, params=params, headers=headers, timeout=30, proxies=proxies)
    response.raise_for_status()
    
    data = response.json()
    events = data.get('data', {}).get('events', [])
    
    return events


def fetch_all_league_matches():
    """
    Fetch matches from all featured basketball leagues.
    
    Returns:
        list: Combined list of all events from all leagues
    """
    all_events = []
    
    print(f"Fetching {SITE_NAME} FEATURED league matches ({len(BASKETBALL_LEAGUE_IDS)} leagues)...", flush=True)
    
    for league_id in BASKETBALL_LEAGUE_IDS:
        try:
            events = fetch_league_matches(league_id)
            all_events.extend(events)
            print(f"   League {league_id}: {len(events)} events")
        except Exception as e:
            print(f"   League {league_id}: Error - {e}")
    
    return all_events


def parse_live_matches(json_data):
    """
    Parse LIVE basketball matches with full odds data from Stoiximan live API.
    
    Args:
        json_data: JSON data from live API endpoint
        
    Returns:
        list: List of dictionaries containing match data with odds
    """
    matches = []
    
    # Extract events, markets, and selections from the JSON
    events = json_data.get('events', {})
    markets_data = json_data.get('markets', {})
    selections_data = json_data.get('selections', {})
    
    for event_id, event in events.items():
        try:
            # Filter for basketball only
            if event.get('sportId') != 'BASK':
                continue
            
            # Get start time
            start_time = event.get('startTime', 0)
            
            # Get participants (teams)
            participants = event.get('participants', [])
            if len(participants) < 2:
                continue
            
            team1_name = participants[0].get('name', 'Unknown')
            team2_name = participants[1].get('name', 'Unknown')
            
            # Skip virtual/esports matches
            virtual_keywords = ['(Esports)', '(esports)', '(E)', '(GODFATHER)', '(KJMR)', 
                              '(RIDER)', '(CARNAGE)', '(CRYPTO)', '(ARCHER)', '(mist)', '(RAMZ)']
            if any(keyword in team1_name or keyword in team2_name for keyword in virtual_keywords):
                continue
            
            # Find 2-way odds (Money Line) using marketIdList and selectionIdList
            team1_odds = 'N/A'
            team2_odds = 'N/A'
            
            # Get market IDs for this event
            market_ids = event.get('marketIdList', [])
            for market_id in market_ids:
                market_id_str = str(market_id)
                if market_id_str not in markets_data:
                    continue
                
                market = markets_data[market_id_str]
                market_name = market.get('name', '')
                
                # Look for Money Line or Match Result market (2-way for basketball)
                if market_name in ['Money Line', 'Match Result', 'Winner']:
                    selection_ids = market.get('selectionIdList', [])
                    
                    # Money Line has 2 selections: Team1, Team2
                    if len(selection_ids) >= 2:
                        for i, sel_id in enumerate(selection_ids[:2]):
                            sel_id_str = str(sel_id)
                            if sel_id_str not in selections_data:
                                continue
                            
                            sel = selections_data[sel_id_str]
                            price = sel.get('price', 'N/A')
                            
                            # First selection is usually Team 1, second is Team 2
                            if i == 0:
                                team1_odds = price
                            elif i == 1:
                                team2_odds = price
                    
                    # Found the Money Line market, no need to check others
                    break
            
            # Build match URL
            event_url = event.get('url', '')
            match_url = f"https://en.stoiximan.gr{event_url}" if event_url else "N/A"
            
            match = {
                'team1': team1_name,
                'team2': team2_name,
                'team1_odds': team1_odds,
                'team2_odds': team2_odds,
                'url': match_url,
                'start_time': start_time,
                'is_live': True
            }
            
            matches.append(match)
            
        except Exception as e:
            print(f"Error parsing live event {event_id}: {e}", flush=True)
            continue
    
    return matches


def parse_league_matches(events):
    """
    Parse featured league basketball matches from Stoiximan league API.
    
    Args:
        events: List of event objects from league API
        
    Returns:
        list: List of dictionaries containing match data with odds
    """
    matches = []
    
    for event in events:
        try:
            # Filter for basketball only
            if event.get('sportId') != 'BASK':
                continue
            
            # Get start time
            start_time = event.get('startTime', 0)
            
            # Get participants (teams)
            participants = event.get('participants', [])
            if len(participants) < 2:
                continue
            
            team1_name = participants[0].get('name', 'Unknown')
            team2_name = participants[1].get('name', 'Unknown')
            
            # Skip virtual/esports matches
            virtual_keywords = ['(Esports)', '(esports)', '(E)', '(GODFATHER)', '(KJMR)', 
                              '(RIDER)', '(CARNAGE)', '(CRYPTO)', '(ARCHER)', '(mist)', '(RAMZ)']
            if any(keyword in team1_name or keyword in team2_name for keyword in virtual_keywords):
                continue
            
            # Find 2-way odds from markets
            team1_odds = None
            team2_odds = None
            
            markets = event.get('markets', [])
            for market in markets:
                # Look for Money Line or Match Result market
                market_type = market.get('type', '')
                market_name = market.get('name', '')
                
                if market_type in ['ML', 'MRES'] or market_name in ['Money Line', 'Match Result', 'Winner']:
                    selections = market.get('selections', [])
                    
                    # For 2-way market, we expect 2 selections
                    if len(selections) >= 2:
                        for i, selection in enumerate(selections[:2]):
                            price = selection.get('price')
                            
                            # First selection is Team 1, second is Team 2
                            if i == 0:
                                team1_odds = price
                            elif i == 1:
                                team2_odds = price
                    break
            
            # Build match URL
            event_url = event.get('url', '')
            match_url = f"https://en.stoiximan.gr{event_url}" if event_url else "N/A"
            
            match = {
                'team1': team1_name,
                'team2': team2_name,
                'team1_odds': team1_odds if team1_odds else 'N/A',
                'team2_odds': team2_odds if team2_odds else 'N/A',
                'url': match_url,
                'start_time': start_time,
                'is_live': False
            }
            
            matches.append(match)
            
        except Exception as e:
            print(f"Error parsing league event: {e}", flush=True)
            continue
    
    return matches


def format_match(match):
    """
    Format a match dictionary into the standard output format.
    Basketball format: 2-way odds (no draw).
    
    Args:
        match: Dictionary containing match data
        
    Returns:
        str: Formatted match string
    """
    team1 = match.get('team1', 'N/A')
    team2 = match.get('team2', 'N/A')
    team1_odds = match.get('team1_odds', 'N/A')
    team2_odds = match.get('team2_odds', 'N/A')
    link_url = match.get('url', 'N/A')
    
    # Format timestamp to Turkish format
    start_time_ms = match.get('start_time', 0)
    start_time_formatted = format_timestamp_turkish(start_time_ms) if start_time_ms else 'N/A'
    
    return (
        f"Team 1: {team1} | Team 2: {team2} | "
        f"Team 1 Win: {team1_odds} | Team 2 Win: {team2_odds} | "
        f"Link: {link_url} | "
        f"Start Time: {start_time_formatted}"
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
        print(f"Fetching {SITE_NAME} basketball matches (live + featured leagues)...")
        print("="*60)
        
        all_matches = []
        
        # Step 1: Fetch LIVE matches
        print("\n1. Fetching LIVE matches...")
        try:
            live_data = fetch_live_matches()
            live_matches = parse_live_matches(live_data)
            all_matches.extend(live_matches)
            print(f"   Found {len(live_matches)} live basketball matches")
        except Exception as e:
            print(f"   Error fetching live matches: {e}")
        
        # Step 2: Fetch FEATURED LEAGUE matches
        print("\n2. Fetching FEATURED LEAGUE matches...")
        try:
            league_events = fetch_all_league_matches()
            league_matches = parse_league_matches(league_events)
            all_matches.extend(league_matches)
            print(f"   Total: {len(league_matches)} featured league matches")
        except Exception as e:
            print(f"   Error fetching league matches: {e}")
        
        # Step 3: Report statistics
        print(f"\n3. Processing results...")
        matches_with_odds = [m for m in all_matches if m['team1_odds'] != 'N/A']
        live_count = sum(1 for m in all_matches if m.get('is_live', False))
        league_count = len(all_matches) - live_count
        
        print(f"   Total matches: {len(all_matches)}")
        print(f"   - Live: {live_count}")
        print(f"   - Featured leagues: {league_count}")
        print(f"   Matches with 2-way odds: {len(matches_with_odds)}")
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
