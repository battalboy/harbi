#!/usr/bin/env python3
"""
Compare Oddswar and Tumbet events to find matches with team name variations.
"""

from rapidfuzz import fuzz
import csv

def load_existing_matches():
    """Load existing matches from tumbet_matches.csv."""
    matches = {}
    try:
        with open('tumbet_matches.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                oddswar = row['Oddswar'].strip()
                tumbet = row['Tumbet'].strip()
                if oddswar and tumbet:
                    matches[oddswar] = tumbet
    except FileNotFoundError:
        pass
    return matches

def parse_formatted_line(line):
    """Parse a formatted event line and extract team names."""
    parts = [p.strip() for p in line.split('|')]
    if len(parts) < 6:
        return None
    
    try:
        team1 = parts[0].split(':', 1)[1].strip()
        team2 = parts[1].split(':', 1)[1].strip()
        return (team1, team2)
    except:
        return None

def teams_similar(team1, team2, threshold=65):
    """Check if two team names are similar using fuzzy matching."""
    return fuzz.ratio(team1.lower(), team2.lower()) >= threshold

def main():
    # Load existing matches from CSV
    existing_matches = load_existing_matches()
    print(f"Loaded {len(existing_matches)} existing matches from tumbet_matches.csv")
    
    # Read Oddswar events
    oddswar_events = []
    with open('oddswar-formatted.txt', 'r', encoding='utf-8') as f:
        for line in f:
            teams = parse_formatted_line(line.strip())
            if teams:
                oddswar_events.append(teams)
    
    # Read Tumbet events
    tumbet_events = []
    with open('tumbet-formatted.txt', 'r', encoding='utf-8') as f:
        for line in f:
            teams = parse_formatted_line(line.strip())
            if teams:
                tumbet_events.append(teams)
    
    print(f"Oddswar events: {len(oddswar_events)}")
    print(f"Tumbet events: {len(tumbet_events)}")
    
    # Find matches where team names are similar but not exact
    matches = []
    
    for oddswar_team1, oddswar_team2 in oddswar_events:
        for tumbet_team1, tumbet_team2 in tumbet_events:
            # Check if both teams match (allowing for fuzzy matching)
            # Also try reversed order in case teams are swapped
            team1_match = teams_similar(oddswar_team1, tumbet_team1)
            team2_match = teams_similar(oddswar_team2, tumbet_team2)
            
            team1_reversed = teams_similar(oddswar_team1, tumbet_team2)
            team2_reversed = teams_similar(oddswar_team2, tumbet_team1)
            
            # Check normal order
            if team1_match and team2_match:
                # Check if names are NOT exactly the same (we want variations)
                # AND check if NOT already in CSV
                already_matched_1 = existing_matches.get(oddswar_team1) == tumbet_team1
                already_matched_2 = existing_matches.get(oddswar_team2) == tumbet_team2
                
                if ((oddswar_team1 != tumbet_team1) or (oddswar_team2 != tumbet_team2)) and not (already_matched_1 and already_matched_2):
                    matches.append({
                        'oddswar': (oddswar_team1, oddswar_team2),
                        'tumbet': (tumbet_team1, tumbet_team2)
                    })
            # Check reversed order
            elif team1_reversed and team2_reversed:
                already_matched_1 = existing_matches.get(oddswar_team1) == tumbet_team2
                already_matched_2 = existing_matches.get(oddswar_team2) == tumbet_team1
                
                if ((oddswar_team1 != tumbet_team2) or (oddswar_team2 != tumbet_team1)) and not (already_matched_1 and already_matched_2):
                    matches.append({
                        'oddswar': (oddswar_team1, oddswar_team2),
                        'tumbet': (tumbet_team2, tumbet_team1)
                    })
    
    # Write results
    with open('temp.txt', 'w', encoding='utf-8') as f:
        for match in matches:
            f.write(f"Oddswar: {match['oddswar'][0]} vs {match['oddswar'][1]}\n")
            f.write(f"Tumbet: {match['tumbet'][0]} vs {match['tumbet'][1]}\n\n")
    
    print(f"Found {len(matches)} event matches with team name variations")
    print(f"Results written to temp.txt")

if __name__ == '__main__':
    main()
