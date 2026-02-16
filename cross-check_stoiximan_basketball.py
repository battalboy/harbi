#!/usr/bin/env python3
"""
Compare Oddswar and Stoiximan basketball events to find matches with team name variations.
"""

from rapidfuzz import fuzz
import csv

def load_existing_matches():
    """Load existing matches from stoiximan_basketball_matches.csv."""
    matches = {}
    try:
        with open('stoiximan_basketball_matches.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                oddswar = row['Oddswar'].strip()
                stoiximan = row['Stoiximan'].strip()
                if oddswar and stoiximan:
                    matches[oddswar] = stoiximan
    except FileNotFoundError:
        pass
    return matches

def parse_formatted_line(line):
    """Parse a formatted event line and extract team names."""
    parts = [p.strip() for p in line.split('|')]
    # Basketball has 5 parts (no draw odds), soccer has 6
    if len(parts) < 5:
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
    print(f"Loaded {len(existing_matches)} existing basketball matches from stoiximan_basketball_matches.csv")
    
    # Read Oddswar basketball events
    oddswar_events = []
    with open('oddswar-basketball-formatted.txt', 'r', encoding='utf-8') as f:
        for line in f:
            teams = parse_formatted_line(line.strip())
            if teams:
                oddswar_events.append(teams)
    
    # Read Stoiximan basketball events
    stoiximan_events = []
    with open('stoiximan-basketball-formatted.txt', 'r', encoding='utf-8') as f:
        for line in f:
            teams = parse_formatted_line(line.strip())
            if teams:
                stoiximan_events.append(teams)
    
    print(f"Oddswar basketball events: {len(oddswar_events)}")
    print(f"Stoiximan basketball events: {len(stoiximan_events)}")
    
    # Find matches where team names are similar but not exact
    matches = []
    
    for oddswar_team1, oddswar_team2 in oddswar_events:
        for stoiximan_team1, stoiximan_team2 in stoiximan_events:
            # Check if both teams match (allowing for fuzzy matching)
            # Also try reversed order in case teams are swapped
            team1_match = teams_similar(oddswar_team1, stoiximan_team1)
            team2_match = teams_similar(oddswar_team2, stoiximan_team2)
            
            team1_reversed = teams_similar(oddswar_team1, stoiximan_team2)
            team2_reversed = teams_similar(oddswar_team2, stoiximan_team1)
            
            # Check normal order
            if team1_match and team2_match:
                # Check if names are NOT exactly the same (we want variations)
                # AND check if NOT already in CSV
                already_matched_1 = existing_matches.get(oddswar_team1) == stoiximan_team1
                already_matched_2 = existing_matches.get(oddswar_team2) == stoiximan_team2
                
                if ((oddswar_team1 != stoiximan_team1) or (oddswar_team2 != stoiximan_team2)) and not (already_matched_1 and already_matched_2):
                    matches.append({
                        'oddswar': (oddswar_team1, oddswar_team2),
                        'stoiximan': (stoiximan_team1, stoiximan_team2)
                    })
            # Check reversed order
            elif team1_reversed and team2_reversed:
                already_matched_1 = existing_matches.get(oddswar_team1) == stoiximan_team2
                already_matched_2 = existing_matches.get(oddswar_team2) == stoiximan_team1
                
                if ((oddswar_team1 != stoiximan_team2) or (oddswar_team2 != stoiximan_team1)) and not (already_matched_1 and already_matched_2):
                    matches.append({
                        'oddswar': (oddswar_team1, oddswar_team2),
                        'stoiximan': (stoiximan_team2, stoiximan_team1)
                    })
    
    # Write results to separate basketball temp file
    with open('temp_basketball.txt', 'w', encoding='utf-8') as f:
        for match in matches:
            f.write(f"Oddswar: {match['oddswar'][0]} vs {match['oddswar'][1]}\n")
            f.write(f"Stoiximan: {match['stoiximan'][0]} vs {match['stoiximan'][1]}\n\n")
    
    print(f"Found {len(matches)} basketball event matches with team name variations")
    print(f"Results written to temp_basketball.txt")

if __name__ == '__main__':
    main()
