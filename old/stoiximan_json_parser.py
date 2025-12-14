"""
Stoiximan JSON API Parser
Extracts soccer match data from Stoiximan JSON API responses
"""

import json
import sys


def parse_json_matches(json_file_path):
    """
    Parse matches from Stoiximan JSON API file.
    
    Args:
        json_file_path (str): Path to the JSON file
        
    Returns:
        list: List of dictionaries containing match data
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
            
            # Try to find odds (if available)
            # Note: In this API structure, markets may not be directly linked
            # This is a simplified extraction focusing on team names
            
            match = {
                'event_id': event_id,
                'team1': team1,
                'team2': team2,
                'team1_odds': 'N/A',
                'draw_odds': 'N/A',
                'team2_odds': 'N/A',
                'league': event.get('leagueId', ''),
                'url': event.get('url', '')
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
        print("Usage: python stoiximan_json_parser.py <input_json_file> [output_file]")
        print("\nExample:")
        print("  python stoiximan_json_parser.py stoiximan-api.json stoiximan-formatted.txt")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'stoiximan-formatted.txt'
    
    print(f"Reading {input_file}...")
    matches = parse_json_matches(input_file)
    
    print(f"Found {len(matches)} soccer matches")
    
    if matches:
        print(f"\nWriting to {output_file}...")
        save_formatted_matches(matches, output_file)
        print(f"✅ Done! {len(matches)} matches saved to {output_file}")
        
        # Show preview
        print("\nPreview (first 5 matches):")
        print("-" * 80)
        for i, match in enumerate(matches[:5], 1):
            print(f"{i}. {format_match(match)}")
    else:
        print("No soccer matches found!")
        sys.exit(1)


if __name__ == '__main__':
    main()

