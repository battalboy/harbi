"""
Complete Stoiximan JSON API Parser with Odds
Extracts soccer match data WITH 1X2 odds from Stoiximan JSON API responses
Can fetch live data directly from API or parse from JSON file
"""

import json
import sys
import requests
import platform
import error_handler


def fetch_stoiximan_data():
    """
    Fetch live match data directly from Stoiximan API.
    
    Returns:
        dict: JSON response with events, markets, selections
    """
    api_url = 'https://en.stoiximan.gr/danae-webapi/api/live/overview/latest'
    params = {
        'includeVirtuals': 'false',
        'queryLanguageId': '1',
        'queryOperatorId': '2'
    }
    
    # Enhanced browser-like headers (without Accept-Encoding to avoid compression issues)
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9,el;q=0.8',
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
    
    print("Fetching live data from Stoiximan API...", flush=True)
    response = requests.get(api_url, params=params, headers=headers, timeout=15, proxies=proxies)
    
    # Raise HTTPError for bad status codes (will be caught with status_code)
    response.raise_for_status()
    
    # Debug: Check content type and first 200 chars
    print(f"Response status: {response.status_code}", flush=True)
    print(f"Content-Type: {response.headers.get('Content-Type', 'Unknown')}", flush=True)
    print(f"Response preview (first 200 chars): {response.text[:200]}", flush=True)
    
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
    
    events = data.get('events', {})
    markets = data.get('markets', {})
    selections = data.get('selections', {})
    
    matches = []
    
    # Extract all events
    for event_id, event in events.items():
        try:
            # Filter for soccer/football
            if event.get('sportId') != 'FOOT':
                continue
            
            # Get participants
            participants = event.get('participants', [])
            if len(participants) < 2:
                continue
            
            team1 = participants[0].get('name', 'Unknown')
            team2 = participants[1].get('name', 'Unknown')
            
            # Skip esports matches
            if '(Esports)' in team1 or '(Esports)' in team2 or \
               '(esports)' in team1 or '(esports)' in team2:
                continue
            
            # Find Match Result market for this event
            market_ids = event.get('marketIdList', [])
            team1_odds = 'N/A'
            draw_odds = 'N/A'
            team2_odds = 'N/A'
            
            for market_id in market_ids:
                market_id_str = str(market_id)
                if market_id_str not in markets:
                    continue
                
                market = markets[market_id_str]
                market_name = market.get('name', '')
                
                # Look for Match Result market
                if market_name == 'Match Result':
                    selection_ids = market.get('selectionIdList', [])
                    
                    # Match Result typically has 3 selections: Team1, Draw, Team2
                    for sel_id in selection_ids:
                        sel_id_str = str(sel_id)
                        if sel_id_str not in selections:
                            continue
                        
                        sel = selections[sel_id_str]
                        sel_name = sel.get('name', '').lower()
                        price = sel.get('price', 'N/A')
                        
                        # Map selection to team or draw
                        if 'draw' in sel_name or sel_name == 'x':
                            draw_odds = price
                        elif team1.lower() in sel_name:
                            team1_odds = price
                        elif team2.lower() in sel_name:
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
            
            match = {
                'event_id': event_id,
                'team1': team1,
                'team2': team2,
                'team1_odds': team1_odds,
                'draw_odds': draw_odds,
                'team2_odds': team2_odds,
                'league_id': event.get('leagueId', ''),
                'url': event.get('url', ''),
                'is_live': event.get('isLive', False),
                'start_time': event.get('startTime', '')
            }
            
            matches.append(match)
            
        except Exception as e:
            print(f"Error parsing event {event_id}: {e}", file=sys.stderr)
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
    """Main function for command-line usage."""
    # Check if input file provided
    if len(sys.argv) >= 2:
        # Read from file mode
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else 'stoiximan-formatted.txt'
        
        print(f"Reading from file: {input_file}...")
        matches = parse_json_matches_with_odds(input_file)
    else:
        # Fetch from API mode
        output_file = 'stoiximan-formatted.txt'
        error_file = 'stoiximan-error.json'
        
        try:
            print("Fetching live data from Stoiximan API...")
            data = fetch_stoiximan_data()
            print(f"✓ Received data from API")
            matches = parse_json_matches_with_odds(data)
            
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if (e.response is not None) else None
            error_info = error_handler.handle_request_error('Stoiximan', e, status_code)
            
            print(f"\n❌ HTTP Error {status_code}: {error_info['error_message']}")
            
            # Write empty output file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('')
            
            # Write error info
            with open(error_file, 'w', encoding='utf-8') as f:
                json.dump(error_info, f, ensure_ascii=False, indent=2)
            
            sys.exit(1)
            
        except requests.exceptions.ConnectionError as e:
            error_info = error_handler.handle_request_error('Stoiximan', e)
            print(f"\n❌ Connection Error: {error_info['error_message']}")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('')
            with open(error_file, 'w', encoding='utf-8') as f:
                json.dump(error_info, f, ensure_ascii=False, indent=2)
            
            sys.exit(1)
            
        except requests.exceptions.Timeout as e:
            error_info = error_handler.handle_request_error('Stoiximan', e)
            print(f"\n❌ Timeout Error: {error_info['error_message']}")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('')
            with open(error_file, 'w', encoding='utf-8') as f:
                json.dump(error_info, f, ensure_ascii=False, indent=2)
            
            sys.exit(1)
            
        except requests.exceptions.JSONDecodeError as e:
            error_info = error_handler.handle_request_error('Stoiximan', e)
            print(f"\n❌ JSON Parse Error: {error_info['error_message']}")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('')
            with open(error_file, 'w', encoding='utf-8') as f:
                json.dump(error_info, f, ensure_ascii=False, indent=2)
            
            sys.exit(1)
            
        except Exception as e:
            error_info = error_handler.handle_request_error('Stoiximan', e)
            print(f"\n❌ Unexpected Error: {error_info['error_message']}")
            print(f"   Technical details: {str(e)}")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('')
            with open(error_file, 'w', encoding='utf-8') as f:
                json.dump(error_info, f, ensure_ascii=False, indent=2)
            
            sys.exit(1)
    
    # Count matches with odds
    matches_with_odds = [m for m in matches if m['team1_odds'] != 'N/A']
    
    print(f"Found {len(matches)} soccer matches")
    print(f"  {len(matches_with_odds)} have Match Result odds")
    print(f"  {len(matches) - len(matches_with_odds)} missing odds")
    
    if matches:
        print(f"\nWriting to {output_file}...")
        save_formatted_matches(matches, output_file)
        print(f"✅ Done! {len(matches)} matches saved to {output_file}")
        
        # Write success to error file
        success_info = error_handler.success_response('Stoiximan')
        with open(error_file, 'w', encoding='utf-8') as f:
            json.dump(success_info, f, ensure_ascii=False, indent=2)
        
        # Show preview of matches WITH odds
        print("\nPreview (matches with odds):")
        print("-" * 80)
        for i, match in enumerate([m for m in matches if m['team1_odds'] != 'N/A'][:5], 1):
            print(f"{i}. {format_match(match)}")
    else:
        print("No soccer matches found!")
        
        # Write error for no events
        error_info = error_handler.handle_request_error('Stoiximan', Exception("NoEventsFound"))
        with open(error_file, 'w', encoding='utf-8') as f:
            json.dump(error_info, f, ensure_ascii=False, indent=2)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('')
        
        sys.exit(1)


if __name__ == '__main__':
    main()

