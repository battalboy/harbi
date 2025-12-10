"""
Oddswar Live Soccer Match Parser

This script fetches live soccer matches from Oddswar's API and extracts:
- Team names
- Match odds (1X2 - only BACK/pink odds, ignoring LAY/blue odds)
- Match links

Output is formatted identically to stoiximan-formatted.txt for easy comparison.
"""

import json
import requests
from typing import List, Dict, Optional


def fetch_markets() -> Dict:
    """
    Fetch the list of in-play soccer markets.
    
    Returns:
        dict: JSON response containing market list
    """
    url = 'https://www.oddswar.com/api/brand/1oddswar/exchange/soccer-1'
    params = {
        'marketTypeId': 'MATCH_ODDS',
        'page': '0',
        'interval': 'inplay',
        'size': '50',
        'setCache': 'false'
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json'
    }
    
    response = requests.get(url, params=params, headers=headers)
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
    
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    return response.json()


def extract_back_odds(runner_prices: List[Dict]) -> Optional[float]:
    """
    Extract the best (first) BACK odds from runner prices.
    We only want BACK odds (pink), not LAY odds (blue).
    
    Args:
        runner_prices: List of price dictionaries
    
    Returns:
        float: Best back price, or None if not available
    """
    back_prices = [p for p in runner_prices if p.get('bet_side') == 'back']
    if back_prices:
        return back_prices[0].get('price')
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
        
        # Get runners (teams + draw)
        runners = market.get('runners', [])
        if len(runners) < 3:
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
        draw_odds = None
        
        if market_id in details_map:
            detail = details_map[market_id]
            detail_runners = detail.get('runners', [])
            
            for runner in detail_runners:
                selection_id = runner.get('selection_id')
                prices = runner.get('prices', [])
                back_odds = extract_back_odds(prices)
                
                # Match selection_id to runner name
                for name, sid in runner_map.items():
                    if sid == selection_id:
                        if name == team1_name:
                            team1_odds = back_odds
                        elif name == team2_name:
                            team2_odds = back_odds
                        elif 'Draw' in name:
                            draw_odds = back_odds
        
        # Build match link
        event_id = event.get('id', '')
        competition = market.get('competition', {})
        comp_id = competition.get('id', '')
        comp_name = competition.get('name', '').lower().replace(' ', '-')
        event_slug = event_name.lower().replace(' v ', '-v-').replace(' ', '-')
        
        match_url = f"/brand/1oddswar/exchange/soccer-1/{comp_name}-{comp_id}/{event_slug}-{event_id}/{market_id}"
        full_url = f"https://www.oddswar.com{match_url}"
        
        match = {
            'id': market_id,
            'team1': team1_name,
            'team2': team2_name,
            'team1_odds': team1_odds,
            'draw_odds': draw_odds,
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
    Format matches stoiximan-formatted.txt exactly.
    
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
    link_url = match.get('full_url', 'N/A')
    
    return (
        f"Team 1: {team1} | Team 2: {team2} | "
        f"Team 1 Win: {team1_odds} | Draw: {draw_odds} | Team 2 Win: {team2_odds} | "
        f"Link: {link_url}"
    )


def save_formatted_matches(matches: List[Dict], output_file: str = 'oddswar-formatted.txt'):
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
    """Main execution function."""
    try:
        print("Fetching Oddswar live soccer matches...")
        
        # Step 1: Fetch market list
        print("\n1. Fetching market list...")
        markets_data = fetch_markets()
        markets = markets_data.get('exchangeMarkets', [])
        print(f"   Found {len(markets)} markets")
        
        if not markets:
            print("No markets found!")
            return
        
        # Step 2: Extract market IDs
        market_ids = [m['id'] for m in markets]
        print(f"\n2. Fetching odds for {len(market_ids)} markets...")
        
        # Fetch details (API can handle multiple market IDs)
        details_data = fetch_market_details(market_ids)
        details = details_data.get('marketDetails', [])
        print(f"   Received odds for {len(details)} markets")
        
        # Step 3: Parse and combine data
        print("\n3. Parsing match data...")
        matches = parse_matches(markets_data, details_data)
        print(f"   Successfully parsed {len(matches)} soccer matches")
        
        # Step 4: Save to file
        print("\n4. Saving formatted output...")
        save_formatted_matches(matches)
        
        print("\n✨ Done!")
        
    except requests.RequestException as e:
        print(f"\n❌ Error fetching data: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

