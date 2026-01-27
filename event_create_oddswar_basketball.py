"""
Oddswar Live Basketball Match Parser

This script fetches live basketball matches from Oddswar's API and extracts:
- Team names
- Match odds (2-way - only LAY/pink odds for arbitrage, ignoring BACK/blue odds)
- Match links

Output is formatted for basketball arbitrage detection.
"""

import json
import requests
from typing import List, Dict, Optional
from error_handler import handle_request_error, success_response, is_ban_indicator


# Constants
SITE_NAME = 'Oddswar'
OUTPUT_FILE = 'oddswar-basketball-formatted.txt'
ERROR_LOG_FILE = 'oddswar-basketball-error.json'


def fetch_markets(interval='inplay', size=50) -> Dict:
    """
    Fetch the list of basketball markets for a given time interval.
    
    Args:
        interval: Time interval - 'inplay' for live, 'today' for today's matches, 'all' for all upcoming
        size: Maximum number of markets to fetch (default 50)
    
    Returns:
        dict: JSON response containing market list
    """
    url = 'https://www.oddswar.com/api/brand/1oddswar/exchange/7522'
    params = {
        'marketTypeId': 'MATCH_ODDS',
        'page': '0',
        'interval': interval,
        'size': str(size),
        'setCache': 'false'
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json'
    }
    
    response = requests.get(url, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_market_details(market_ids: List[str]) -> Dict:
    """
    Fetch detailed odds for specific markets.
    
    Args:
        market_ids: List of market IDs to fetch details for
    
    Returns:
        dict: JSON response containing market details with odds
    """
    url = 'https://www.oddswar.com/api/brand/1oddswar/exchange/marketDetails'
    
    # Build query params: marketIds[0]=xxx&marketIds[1]=yyy
    params = {f'marketIds[{i}]': mid for i, mid in enumerate(market_ids)}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json'
    }
    
    response = requests.get(url, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


def extract_lay_odds(runner_prices: List[Dict]) -> Optional[float]:
    """
    Extract the best (first) LAY odds from runner prices.
    For arbitrage, we need LAY odds (pink) from Oddswar where we act as bookmaker.
    We ignore BACK odds (blue).
    
    Args:
        runner_prices: List of price dictionaries
    
    Returns:
        float: Best lay price, or None if not available
    """
    lay_prices = [p for p in runner_prices if p.get('bet_side') == 'lay']
    if lay_prices:
        return lay_prices[0].get('price')
    return None


def parse_matches(markets_data: Dict, details_data: Dict) -> List[Dict]:
    """
    Parse match data from both API responses and extract match information.
    
    Args:
        markets_data: Response from markets list API
        details_data: Response from market details API
    
    Returns:
        List of match dictionaries with team names, odds, and links
    """
    matches = []
    
    # Create a lookup map of market_id -> market_details
    details_map = {}
    if details_data and 'marketDetails' in details_data:
        for detail in details_data['marketDetails']:
            details_map[detail['marketId']] = detail
    
    # Process each market
    markets = markets_data.get('exchangeMarkets', [])
    for market in markets:
        market_id = market.get('id')
        event = market.get('event', {})
        event_name = event.get('name', '')
        
        # Parse team names from event name (format: "Team1 v Team2")
        if ' v ' not in event_name:
            continue
        
        teams = event_name.split(' v ')
        if len(teams) != 2:
            continue
        
        team1_name = teams[0].strip()
        team2_name = teams[1].strip()
        
        # Get runners (2 teams for basketball - no draw)
        runners = market.get('runners', [])
        if len(runners) < 2:
            continue
        
        # Map runner names to their selection IDs
        runner_map = {}
        for runner in runners:
            runner_name = runner.get('runnerName')
            selection_id = runner.get('selectionId')
            runner_map[runner_name] = selection_id
        
        # Find odds from details
        team1_odds = None
        team2_odds = None
        
        if market_id in details_map:
            detail = details_map[market_id]
            detail_runners = detail.get('runners', [])
            
            for runner in detail_runners:
                selection_id = runner.get('selection_id')
                prices = runner.get('prices', [])
                lay_odds = extract_lay_odds(prices)
                
                # Match selection_id to runner name
                for name, sid in runner_map.items():
                    if sid == selection_id:
                        if name == team1_name:
                            team1_odds = lay_odds
                        elif name == team2_name:
                            team2_odds = lay_odds
        
        # Build match link
        event_id = event.get('id', '')
        competition = market.get('competition', {})
        comp_id = competition.get('id', '')
        comp_name = competition.get('name', '').lower().replace(' ', '-')
        event_slug = event_name.lower().replace(' v ', '-v-').replace(' ', '-')
        
        match_url = f"/brand/1oddswar/exchange/7522/{comp_name}-{comp_id}/{event_slug}-{event_id}/{market_id}"
        full_url = f"https://www.oddswar.com{match_url}"
        
        match = {
            'id': market_id,
            'team1': team1_name,
            'team2': team2_name,
            'team1_odds': team1_odds,
            'team2_odds': team2_odds,
            'competition': competition.get('name', ''),
            'url': match_url,
            'full_url': full_url,
            'start_time': event.get('openDate', '')
        }
        
        matches.append(match)
    
    return matches


def format_match(match: Dict) -> str:
    """
    Format a match dictionary into a human-readable string.
    Basketball format: 2-way odds (no draw).
    
    Args:
        match: A dictionary containing match data
    
    Returns:
        str: A formatted string representing the match
    """
    team1 = match.get('team1', 'N/A')
    team2 = match.get('team2', 'N/A')
    team1_odds = match.get('team1_odds', 'N/A')
    team2_odds = match.get('team2_odds', 'N/A')
    link_url = match.get('full_url', 'N/A')
    
    return (
        f"Team 1: {team1} | Team 2: {team2} | "
        f"Team 1 Win: {team1_odds} | Team 2 Win: {team2_odds} | "
        f"Link: {link_url}"
    )


def save_formatted_matches(matches: List[Dict], output_file: str = 'oddswar-basketball-formatted.txt'):
    """
    Save formatted matches to a text file.
    File is overwritten each time to ensure only latest data.
    
    Args:
        matches: List of match dictionaries
        output_file: Output filename
    """
    with open(output_file, 'w') as f:
        for match in matches:
            f.write(format_match(match) + '\n')
    
    print(f"\n✅ Saved {len(matches)} matches to {output_file}")


def main():
    """Main execution function with comprehensive error handling."""
    try:
        print(f"Fetching {SITE_NAME} live and upcoming basketball matches...")
        
        all_markets = []
        all_market_ids = []
        
        # Step 1: Fetch LIVE (in-play) markets
        print("\n1. Fetching LIVE (in-play) markets...")
        try:
            inplay_data = fetch_markets(interval='inplay', size=50)
            inplay_markets = inplay_data.get('exchangeMarkets', [])
            all_markets.extend(inplay_markets)
            all_market_ids.extend([m['id'] for m in inplay_markets])
            print(f"   Found {len(inplay_markets)} live markets")
        except Exception as e:
            print(f"   Error fetching live markets: {e}")
        
        # Step 2: Fetch TODAY's upcoming markets
        print("\n2. Fetching TODAY's upcoming markets...")
        try:
            today_data = fetch_markets(interval='today', size=100)
            today_markets = today_data.get('exchangeMarkets', [])
            
            # Filter out duplicates (markets already in live)
            existing_ids = set(all_market_ids)
            new_today_markets = [m for m in today_markets if m['id'] not in existing_ids]
            
            all_markets.extend(new_today_markets)
            all_market_ids.extend([m['id'] for m in new_today_markets])
            print(f"   Found {len(new_today_markets)} new today markets ({len(today_markets)} total, {len(today_markets) - len(new_today_markets)} duplicates)")
        except Exception as e:
            print(f"   Error fetching today markets: {e}")
        
        # Step 3: Fetch ALL upcoming markets (next few days)
        print("\n3. Fetching ALL upcoming markets...")
        try:
            all_data = fetch_markets(interval='all', size=200)
            all_upcoming = all_data.get('exchangeMarkets', [])
            
            # Filter out duplicates
            existing_ids = set(all_market_ids)
            new_upcoming = [m for m in all_upcoming if m['id'] not in existing_ids]
            
            all_markets.extend(new_upcoming)
            all_market_ids.extend([m['id'] for m in new_upcoming])
            print(f"   Found {len(new_upcoming)} new upcoming markets ({len(all_upcoming)} total, {len(all_upcoming) - len(new_upcoming)} duplicates)")
        except Exception as e:
            print(f"   Error fetching all markets: {e}")
        
        if not all_markets:
            print("\n⚠️  No markets found!")
            # Write empty output file
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                f.write('')
            # Write NoEventsFound status
            error_info = handle_request_error(SITE_NAME, Exception("NoEventsFound"))
            with open(ERROR_LOG_FILE, 'w', encoding='utf-8') as f:
                json.dump(error_info, f, ensure_ascii=False, indent=2)
            return error_info
        
        print(f"\n📊 Total unique markets: {len(all_markets)}")
        
        # Step 4: Fetch odds for all markets
        print(f"\n4. Fetching odds for {len(all_market_ids)} markets...")
        details_data = fetch_market_details(all_market_ids)
        details = details_data.get('marketDetails', [])
        print(f"   Received odds for {len(details)} markets")
        
        # Step 5: Parse and combine data
        print("\n5. Parsing match data...")
        # Combine all markets into a single structure
        combined_data = {'exchangeMarkets': all_markets}
        matches = parse_matches(combined_data, details_data)
        print(f"   Successfully parsed {len(matches)} basketball matches")
        
        # Step 6: Save to file
        print("\n6. Saving formatted output...")
        save_formatted_matches(matches, OUTPUT_FILE)
        
        # Write success status
        success_info = success_response(SITE_NAME)
        with open(ERROR_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(success_info, f, ensure_ascii=False, indent=2)
        
        print("\n✨ Done!")
        return success_info
        
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
