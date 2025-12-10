#!/usr/bin/env python3
"""
Create matches.csv with Oddswar team names and their probable Stoiximan matches.
Uses fuzzy matching (rapidfuzz) to find best matches.
"""

import csv
from rapidfuzz import fuzz, process


def load_team_names(filename):
    """Load team names from a text file."""
    with open(filename, 'r', encoding='utf-8') as f:
        teams = [line.strip() for line in f if line.strip()]
    return teams


def find_best_match(oddswar_team, stoiximan_teams, threshold=80):
    """
    Find the best matching Stoiximan team name for an Oddswar team.
    
    Args:
        oddswar_team: Team name from Oddswar
        stoiximan_teams: List of team names from Stoiximan
        threshold: Minimum similarity score (0-100) to consider a match
    
    Returns:
        Tuple of (matched_team, score) or (None, 0) if no good match
    """
    if not stoiximan_teams:
        return None, 0
    
    # Use fuzz.ratio for overall similarity
    result = process.extractOne(
        oddswar_team,
        stoiximan_teams,
        scorer=fuzz.ratio
    )
    
    if result and result[1] >= threshold:
        return result[0], result[1]
    
    return None, 0


def create_matches_csv():
    """Create matches.csv with Oddswar and probable Stoiximan matches."""
    
    print("📂 Loading team names...")
    oddswar_teams = load_team_names('oddswar_names_full.txt')
    stoiximan_teams = load_team_names('stoiximan_names.txt')
    
    print(f"   Oddswar teams: {len(oddswar_teams)}")
    print(f"   Stoiximan teams: {len(stoiximan_teams)}")
    
    print("\n🔍 Matching teams (threshold: 80%)...")
    print("   ℹ️  Each Stoiximan team can only be matched once (prevents duplicates)")
    
    # Track which Stoiximan teams have been used
    available_stoiximan_teams = stoiximan_teams.copy()
    
    matches = []
    match_count = 0
    
    for i, oddswar_team in enumerate(oddswar_teams, 1):
        # Only search among teams that haven't been matched yet
        stoiximan_match, score = find_best_match(oddswar_team, available_stoiximan_teams)
        
        if stoiximan_match:
            match_count += 1
            if score < 100:  # Show non-exact matches
                print(f"   [{score:.0f}%] {oddswar_team} → {stoiximan_match}")
            
            # Remove the matched team from available pool
            available_stoiximan_teams.remove(stoiximan_match)
        
        matches.append({
            'Oddswar': oddswar_team,
            'Stoiximan': stoiximan_match if stoiximan_match else ''
        })
        
        # Progress indicator
        if i % 100 == 0:
            print(f"   Processed {i}/{len(oddswar_teams)} teams...")
    
    print(f"\n📝 Writing to matches.csv...")
    
    with open('matches.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Oddswar', 'Stoiximan'])
        writer.writeheader()
        writer.writerows(matches)
    
    print(f"\n✅ Done!")
    print(f"{'='*60}")
    print(f"📊 Results:")
    print(f"   Total Oddswar teams: {len(oddswar_teams)}")
    print(f"   Matches found: {match_count}")
    print(f"   No match: {len(oddswar_teams) - match_count}")
    print(f"   Match rate: {(match_count/len(oddswar_teams)*100):.1f}%")
    print(f"\n📄 Output: matches.csv")
    print(f"{'='*60}")


if __name__ == '__main__':
    create_matches_csv()

