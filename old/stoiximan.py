"""
Stoiximan HTML Parser
Extracts soccer match data from Stoiximan betting site HTML.

This script parses HTML content to extract:
- Team names
- Betting odds (Team 1 win, Draw, Team 2 win)

Usage:
    python stoiximan.py input.html output.txt
    
    Or use as a module:
    from stoiximan import parse_matches
    matches = parse_matches('stoiximan.txt')
"""

from bs4 import BeautifulSoup
import re
import sys


def parse_matches(html_file_path):
    """
    Parse matches from HTML file.
    
    Args:
        html_file_path (str): Path to the HTML file
        
    Returns:
        list: List of dictionaries containing match data
    """
    # Read the HTML
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'lxml')
    
    # Find all event cards
    event_cards = soup.find_all('div', {'data-qa': 'event-card'})
    
    matches = []
    
    for i, card in enumerate(event_cards, 1):
        try:
            # Get team names from participants
            participants = card.find('div', {'data-qa': 'participants'})
            if not participants:
                print(f"  Match {i}: No participants found, skipping", file=sys.stderr)
                continue
            
            # Find team name divs - they have specific classes
            team_divs = participants.find_all('div', class_='tw-truncate')
            
            if len(team_divs) >= 2:
                team1 = team_divs[0].get_text(strip=True)
                team2 = team_divs[1].get_text(strip=True)
            else:
                print(f"  Match {i}: Could not find team names, skipping", file=sys.stderr)
                continue
            
            # Get odds
            selections = card.find_all('div', {'data-qa': 'event-selection'})
            if len(selections) < 3:
                print(f"  Match {i}: Not enough odds found ({len(selections)}), skipping", file=sys.stderr)
                continue
            
            # Extract odds values
            odds = []
            for sel in selections[:3]:
                odd_text = sel.get_text(strip=True)
                # Remove 'X' prefix if present (for draw odds)
                odd_text = odd_text.replace('X', '')
                # Keep only numbers and dots
                odd_text = re.sub(r'[^0-9.]', '', odd_text)
                odds.append(odd_text)
            
            team1_odds = odds[0] if len(odds) > 0 else "N/A"
            draw_odds = odds[1] if len(odds) > 1 else "N/A"
            team2_odds = odds[2] if len(odds) > 2 else "N/A"
            
            # Create match dictionary
            match = {
                'team1': team1,
                'team2': team2,
                'team1_odds': team1_odds,
                'draw_odds': draw_odds,
                'team2_odds': team2_odds
            }
            
            matches.append(match)
            
        except Exception as e:
            print(f"  Match {i}: Error - {e}", file=sys.stderr)
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
        print("Usage: python stoiximan.py <input_html_file> [output_file]")
        print("\nExample:")
        print("  python stoiximan.py stoiximan.txt stoiximan-formatted.txt")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'stoiximan-formatted.txt'
    
    print(f"Reading {input_file}...")
    matches = parse_matches(input_file)
    
    print(f"Found {len(matches)} matches")
    
    if matches:
        print(f"\nWriting to {output_file}...")
        save_formatted_matches(matches, output_file)
        print(f"✅ Done! {len(matches)} matches saved to {output_file}")
        
        # Show preview
        print("\nPreview (first 3 matches):")
        print("-" * 80)
        for i, match in enumerate(matches[:3], 1):
            print(f"{i}. {format_match(match)}")
    else:
        print("No matches found!")
        sys.exit(1)


if __name__ == '__main__':
    main()

