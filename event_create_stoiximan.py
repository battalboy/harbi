"""
Complete Stoiximan JSON API Parser with Odds
Extracts soccer match data WITH 1X2 odds from Stoiximan JSON API responses
Can fetch live data directly from API or parse from JSON file
"""

import json
import sys
import platform
import requests
from error_handler import handle_request_error, success_response, is_ban_indicator


# Constants
SITE_NAME = 'Stoiximan'
OUTPUT_FILE = 'stoiximan-formatted.txt'
ERROR_LOG_FILE = 'stoiximan-error.json'


def fetch_stoiximan_data(league_id):
    """
    Fetch match data directly from Stoiximan API.
    
    Args:
        league_id (str): Stoiximan internal league ID
    
    Returns:
        dict: JSON response with events, markets, selections
    """
    api_url = f'https://en.stoiximan.gr/api/league/hot/upcoming?leagueId={league_id}&req=s,stnf,c,mb'
    params = {
        'includeVirtuals': 'false',
        'queryLanguageId': '1',
        'queryOperatorId': '2'
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://en.stoiximan.gr/',
        'Origin': 'https://en.stoiximan.gr',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }
    
    # Use Gluetun proxy on Linux, direct connection on macOS
    proxies = None
    if platform.system() == 'Linux':
        proxies = {
            'http': 'http://127.0.0.1:8888',   # Greece VPN for Stoiximan
            'https': 'http://127.0.0.1:8888'
        }
        print("Using Gluetun Greece proxy (Linux)...", flush=True)
    else:
        print("Using direct connection (macOS/ExpressVPN app)...", flush=True)
    
    print(f"Fetching prematch data from Stoiximan API for league {league_id}...", flush=True)
    response = requests.get(api_url, headers=headers, timeout=15, proxies=proxies)
    
    # Raise HTTPError for bad status codes (will be caught with status_code)
    response.raise_for_status()
    
    return response.json()


def parse_json_matches_with_odds(json_data):
    """
    Parse matches with full odds data from Stoiximan JSON API data.
    
    Args:
        json_data (dict or str): JSON data dict (from API) or file path string
        
    Returns:
        list: List of dictionaries containing match data with odds
    """
    # If json_data is a string, assume it's a file path and load it
    if isinstance(json_data, str):
        with open(json_data, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = json_data
    
    # Adjusted parsing for the new API structure
    events_data = data.get('data', {}).get('events', [])
    
    matches = []
    
    # Extract all events
    for event in events_data:
        try:
            # Filter for soccer/football
            if event.get('sportId') != 'FOOT':
                continue
            
            # Get team names from event name (format: "Team 1 - Team 2")
            event_name = event.get('name', '')
            if ' - ' not in event_name:
                continue
            
            parts = event_name.split(' - ', 1)
            if len(parts) < 2:
                continue
            
            team1 = parts[0].strip()
            team2 = parts[1].strip()
            
            # Skip esports matches
            if '(Esports)' in team1 or '(Esports)' in team2 or \
               '(esports)' in team1 or '(esports)' in team2:
                continue
            
            # Find Match Result market for this event
            team1_odds = 'N/A'
            draw_odds = 'N/A'
            team2_odds = 'N/A'
            
            for market in event.get('markets', []):
                if market.get('type') == 'MRES':  # Match Result market
                    for sel in market.get('selections', []):
                        sel_name = sel.get('name', '').lower()
                        price = sel.get('price', 'N/A')
                        
                        if sel_name == '1':
                            team1_odds = price
                        elif sel_name == 'x':
                            draw_odds = price
                        elif sel_name == '2':
                            team2_odds = price
                    break  # Found MRES, no need to check other markets
            
            match = {
                'event_id': event.get('id'),
                'team1': team1,
                'team2': team2,
                'team1_odds': team1_odds,
                'draw_odds': draw_odds,
                'team2_odds': team2_odds,
                'league_id': event.get('leagueId', ''),
                'url': event.get('url', ''),
                'is_live': False,  # Prematch endpoint
                'start_time': event.get('startTime', '')
            }
            
            matches.append(match)
            
        except Exception as e:
            print(f"Error parsing event {event.get('id')}: {e}", file=sys.stderr)
            continue
    
    return matches


def format_match(match):
    """
    Format a match dictionary into a human-readable string.
    
    Args:
        match (dict): Match data dictionary
        
    Returns:
        str: Formatted match string
    """
    # Build full URL
    url = match.get('url', '')
    full_url = f"https://en.stoiximan.gr{url}" if url else 'N/A'
    
    return (f"Team 1: {match['team1']} | "
            f"Team 2: {match['team2']} | "
            f"Team 1 Win: {match['team1_odds']} | "
            f"Draw: {match['draw_odds']} | "
            f"Team 2 Win: {match['team2_odds']} | "
            f"Link: {full_url}")


def save_formatted_matches(matches, output_file_path):
    """
    Save formatted matches to a text file.
    
    Args:
        matches (list): List of match dictionaries
        output_file_path (str): Path to output file
    """
    with open(output_file_path, 'w', encoding='utf-8') as f:
        for match in matches:
            f.write(format_match(match) + '\n')


def main():
    """Main function for command-line usage with comprehensive error handling."""
    # Default league ID for testing (Champions League)
    default_league_id = "182748"
    
    # Check if input file provided
    if len(sys.argv) >= 2:
        # Read from file mode
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else OUTPUT_FILE
        
        print(f"Reading from file: {input_file}...")
        try:
            matches = parse_json_matches_with_odds(input_file)
        except Exception as e:
            error_info = handle_request_error(SITE_NAME, e)
            print(f"\n❌ Error parsing file: {error_info['error_message']}")
            with open(ERROR_LOG_FILE, 'w', encoding='utf-8') as f:
                json.dump(error_info, f, ensure_ascii=False, indent=2)
            sys.exit(1)
    else:
        # Fetch from API mode
        output_file = OUTPUT_FILE
        
        try:
            print(f"Fetching prematch data from {SITE_NAME} API...")
            data = fetch_stoiximan_data(default_league_id)
            print(f"✓ Received data from API")
            matches = parse_json_matches_with_odds(data)
            
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
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('')
            
            sys.exit(1)
            
        except requests.exceptions.ConnectionError as e:
            error_info = handle_request_error(SITE_NAME, e)
            print(f"\n❌ Connection Error: {error_info['error_message']}")
            
            with open(ERROR_LOG_FILE, 'w', encoding='utf-8') as f:
                json.dump(error_info, f, ensure_ascii=False, indent=2)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('')
            
            sys.exit(1)
            
        except requests.exceptions.Timeout as e:
            error_info = handle_request_error(SITE_NAME, e)
            print(f"\n❌ Timeout Error: {error_info['error_message']}")
            
            with open(ERROR_LOG_FILE, 'w', encoding='utf-8') as f:
                json.dump(error_info, f, ensure_ascii=False, indent=2)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('')
            
            sys.exit(1)
            
        except json.JSONDecodeError as e:
            error_info = handle_request_error(SITE_NAME, e)
            print(f"\n❌ JSON Parse Error: {error_info['error_message']}")
            
            with open(ERROR_LOG_FILE, 'w', encoding='utf-8') as f:
                json.dump(error_info, f, ensure_ascii=False, indent=2)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('')
            
            sys.exit(1)
            
        except Exception as e:
            error_info = handle_request_error(SITE_NAME, e)
            print(f"\n❌ Unexpected Error: {error_info['error_message']}")
            print(f"   Technical details: {str(e)}")
            
            with open(ERROR_LOG_FILE, 'w', encoding='utf-8') as f:
                json.dump(error_info, f, ensure_ascii=False, indent=2)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('')
            
            sys.exit(1)
    
    # Count matches with odds
    matches_with_odds = [m for m in matches if m['team1_odds'] != 'N/A']
    
    print(f"Found {len(matches)} soccer matches")
    print(f"  {len(matches_with_odds)} have Match Result odds")
    print(f"  {len(matches) - len(matches_with_odds)} missing odds")
    
    if matches:
        print(f"\nWriting to {output_file}...")
        save_formatted_matches(matches, output_file)
        
        # Write success status
        success_info = success_response(SITE_NAME)
        with open(ERROR_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(success_info, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Done! {len(matches)} matches saved to {output_file}")
        
        # Show preview of matches WITH odds
        print("\nPreview (matches with odds):")
        print("-" * 80)
        for i, match in enumerate([m for m in matches if m['team1_odds'] != 'N/A'][:5], 1):
            print(f"{i}. {format_match(match)}")
    else:
        print("⚠️ No soccer matches found!")
        # Write empty output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('')
        # Write NoEventsFound status
        error_info = handle_request_error(SITE_NAME, Exception("NoEventsFound"))
        with open(ERROR_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(error_info, f, ensure_ascii=False, indent=2)
        sys.exit(1)


if __name__ == '__main__':
    main()

