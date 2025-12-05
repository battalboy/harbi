"""
Complete Stoiximan JSON API Parser with Odds
Extracts soccer match data WITH 1X2 odds from Stoiximan JSON API responses
"""

import json
import sys


def parse_json_matches_with_odds(json_file_path):
    """
    Parse matches with full odds data from Stoiximan JSON API file.
    
    Args:
        json_file_path (str): Path to the JSON file
        
    Returns:
        list: List of dictionaries containing match data with odds
    """
    # Load JSON
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
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
    return (f"Team 1: {match['team1']} | "
            f"Team 2: {match['team2']} | "
            f"Team 1 Win: {match['team1_odds']} | "
            f"Draw: {match['draw_odds']} | "
            f"Team 2 Win: {match['team2_odds']}")


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
    if len(sys.argv) < 2:
        print("Usage: python stoiximan_api_complete_parser.py <input_json_file> [output_file]")
        print("\nExample:")
        print("  python stoiximan_api_complete_parser.py stoiximan-api.json stoiximan-formatted.txt")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'stoiximan-formatted.txt'
    
    print(f"Reading {input_file}...")
    matches = parse_json_matches_with_odds(input_file)
    
    # Count matches with odds
    matches_with_odds = [m for m in matches if m['team1_odds'] != 'N/A']
    
    print(f"Found {len(matches)} soccer matches")
    print(f"  {len(matches_with_odds)} have Match Result odds")
    print(f"  {len(matches) - len(matches_with_odds)} missing odds")
    
    if matches:
        print(f"\nWriting to {output_file}...")
        save_formatted_matches(matches, output_file)
        print(f"✅ Done! {len(matches)} matches saved to {output_file}")
        
        # Show preview of matches WITH odds
        print("\nPreview (matches with odds):")
        print("-" * 80)
        for i, match in enumerate([m for m in matches if m['team1_odds'] != 'N/A'][:5], 1):
            print(f"{i}. {format_match(match)}")
    else:
        print("No soccer matches found!")
        sys.exit(1)


if __name__ == '__main__':
    main()

