#!/usr/bin/env python3
"""
Compare Oddswar and Roobet basketball events to find matches with team name variations.
"""

from rapidfuzz import fuzz
import csv

def load_existing_matches():
    """Load existing matches from roobet_basketball_matches.csv."""
    matches = {}
    try:
        with open('roobet_basketball_matches.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                oddswar = row['Oddswar'].strip()
                roobet = row['Roobet'].strip()
                if oddswar and roobet:
                    matches[oddswar] = roobet
    except FileNotFoundError:
        pass
    return matches

def parse_formatted_line(line):
    """Parse a formatted event line and extract team names."""
    parts = [p.strip() for p in line.split('|')]
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
    existing_matches = load_existing_matches()
    print(f"Loaded {len(existing_matches)} existing basketball matches from roobet_basketball_matches.csv")
    
    oddswar_events = []
    with open('oddswar-basketball-formatted.txt', 'r', encoding='utf-8') as f:
        for line in f:
            teams = parse_formatted_line(line.strip())
            if teams:
                oddswar_events.append(teams)
    
    roobet_events = []
    with open('roobet-basketball-formatted.txt', 'r', encoding='utf-8') as f:
        for line in f:
            teams = parse_formatted_line(line.strip())
            if teams:
                roobet_events.append(teams)
    
    print(f"Oddswar basketball events: {len(oddswar_events)}")
    print(f"Roobet basketball events: {len(roobet_events)}")
    print(f"Processing {len(oddswar_events) * len(roobet_events)} comparisons...")
    
    matches = []
    
    for idx, (oddswar_team1, oddswar_team2) in enumerate(oddswar_events):
        if idx % 10 == 0:
            print(f"  Progress: {idx}/{len(oddswar_events)} events checked...", flush=True)
        
        for roobet_team1, roobet_team2 in roobet_events:
            team1_match = teams_similar(oddswar_team1, roobet_team1)
            team2_match = teams_similar(oddswar_team2, roobet_team2)
            
            team1_reversed = teams_similar(oddswar_team1, roobet_team2)
            team2_reversed = teams_similar(oddswar_team2, roobet_team1)
            
            if team1_match and team2_match:
                already_matched_1 = existing_matches.get(oddswar_team1) == roobet_team1
                already_matched_2 = existing_matches.get(oddswar_team2) == roobet_team2
                
                if ((oddswar_team1 != roobet_team1) or (oddswar_team2 != roobet_team2)) and not (already_matched_1 and already_matched_2):
                    matches.append({
                        'oddswar': (oddswar_team1, oddswar_team2),
                        'roobet': (roobet_team1, roobet_team2)
                    })
            elif team1_reversed and team2_reversed:
                already_matched_1 = existing_matches.get(oddswar_team1) == roobet_team2
                already_matched_2 = existing_matches.get(oddswar_team2) == roobet_team1
                
                if ((oddswar_team1 != roobet_team2) or (oddswar_team2 != roobet_team1)) and not (already_matched_1 and already_matched_2):
                    matches.append({
                        'oddswar': (oddswar_team1, oddswar_team2),
                        'roobet': (roobet_team2, roobet_team1)
                    })
    
    with open('temp_basketball.txt', 'w', encoding='utf-8') as f:
        for match in matches:
            f.write(f"Oddswar: {match['oddswar'][0]} vs {match['oddswar'][1]}\n")
            f.write(f"Roobet: {match['roobet'][0]} vs {match['roobet'][1]}\n\n")
    
    print(f"Found {len(matches)} basketball event matches with team name variations")
    print(f"Results written to temp_basketball.txt")

if __name__ == '__main__':
    main()
