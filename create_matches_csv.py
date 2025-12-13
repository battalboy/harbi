#!/usr/bin/env python3
"""
Create matches.csv with Oddswar team names and their probable Stoiximan matches.
Uses fuzzy matching (rapidfuzz) to find best matches.
"""

import csv
import re
from rapidfuzz import fuzz, process


def load_team_names(filename):
    """Load team names from a text file."""
    with open(filename, 'r', encoding='utf-8') as f:
        teams = [line.strip() for line in f if line.strip()]
    return teams


def extract_indicators(team_name):
    """
    Extract age/gender indicators from team name.
    
    Returns:
        Set of indicators found (e.g., {'U19', '(W)'} or empty set)
    """
    indicators = set()
    
    # Check for age groups: U19, U20, U21, U23
    age_pattern = r'\b(U19|U20|U21|U23)\b'
    age_matches = re.findall(age_pattern, team_name, re.IGNORECASE)
    indicators.update([m.upper() for m in age_matches])
    
    # Check for women's teams: (W)
    if '(W)' in team_name or '(w)' in team_name:
        indicators.add('(W)')
    
    return indicators


def find_best_match(oddswar_team, stoiximan_teams, threshold=80):
    """
    Find the best matching Stoiximan team name for an Oddswar team.
    
    Args:
        oddswar_team: Team name from Oddswar
        stoiximan_teams: List of team names from Stoiximan (already filtered for duplicates)
        threshold: Minimum similarity score (0-100) to consider a match
    
    Returns:
        Tuple of (matched_team, score) or (None, 0) if no good match
    """
    if not stoiximan_teams:
        return None, 0
    
    # Extract indicators from the Oddswar team name
    oddswar_indicators = extract_indicators(oddswar_team)
    
    # Filter Stoiximan teams to only those with matching indicators
    indicator_filtered_teams = [
        t for t in stoiximan_teams 
        if extract_indicators(t) == oddswar_indicators
    ]
    
    # If no teams match the indicator criteria, return no match
    if not indicator_filtered_teams:
        return None, 0
    
    # Use fuzz.ratio for overall similarity on the filtered list
    result = process.extractOne(
        oddswar_team,
        indicator_filtered_teams,
        scorer=fuzz.ratio
    )
    
    if result and result[1] >= threshold:
        return result[0], result[1]
    
    return None, 0


def create_matches_csv():
    """Create matches.csv with Oddswar and probable Stoiximan matches."""
    
    print("📂 Loading team names...")
    oddswar_teams = load_team_names('oddswar_names.txt')
    stoiximan_teams = load_team_names('stoiximan_names.txt')
    
    print(f"   Oddswar teams: {len(oddswar_teams)}")
    print(f"   Stoiximan teams: {len(stoiximan_teams)}")
    
    # Load existing matches if CSV already exists
    existing_matches = {}  # Maps Oddswar -> {'Stoiximan': name, 'Confidence': score}
    already_used_stoiximan = set()
    csv_exists = False
    
    try:
        with open('matches.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                oddswar = row['Oddswar']
                stoiximan = row.get('Stoiximan', '')
                confidence = row.get('Confidence', '')
                existing_matches[oddswar] = {
                    'Stoiximan': stoiximan,
                    'Confidence': confidence
                }
                if stoiximan:  # Track already-used Stoiximan teams
                    already_used_stoiximan.add(stoiximan)
        csv_exists = True
        print(f"\n📄 Found existing matches.csv")
        print(f"   Preserving {len([m for m in existing_matches.values() if m['Stoiximan']])} existing matches")
        print(f"   {len(already_used_stoiximan)} Stoiximan teams already matched")
    except FileNotFoundError:
        print(f"\n📄 No existing matches.csv found - will create new file")
    
    print("\n🔍 Matching teams (threshold: 80%)...")
    print("   ℹ️  Each Stoiximan team can only be matched once (prevents duplicates)")
    print("   ℹ️  Preserving existing matches - only filling in blanks")
    print("   ℹ️  Enforcing indicator matching (U19/U20/U21/U23/(W) must match)")
    
    # Track which Stoiximan teams are available (not already used)
    available_stoiximan_teams = [t for t in stoiximan_teams if t not in already_used_stoiximan]
    print(f"   ℹ️  Available for new matches: {len(available_stoiximan_teams)} Stoiximan teams")
    
    matches = []
    new_match_count = 0
    preserved_count = 0
    
    for i, oddswar_team in enumerate(oddswar_teams, 1):
        # Check if this Oddswar team already has a match
        if csv_exists and oddswar_team in existing_matches and existing_matches[oddswar_team]['Stoiximan']:
            # Preserve existing match AND confidence
            match_data = existing_matches[oddswar_team]
            stoiximan_match = match_data['Stoiximan']
            confidence = match_data['Confidence']
            preserved_count += 1
        else:
            # Only search among teams that haven't been matched yet
            stoiximan_match, score = find_best_match(oddswar_team, available_stoiximan_teams)
            
            if stoiximan_match:
                new_match_count += 1
                confidence = f"{score:.1f}"
                if score < 100:  # Show non-exact matches
                    print(f"   [{score:.0f}%] {oddswar_team} → {stoiximan_match}")
                
                # Remove the matched team from available pool
                available_stoiximan_teams.remove(stoiximan_match)
            else:
                stoiximan_match = None
                confidence = ''
        
        matches.append({
            'Oddswar': oddswar_team,
            'Stoiximan': stoiximan_match if stoiximan_match else '',
            'Confidence': confidence
        })
        
        # Progress indicator
        if i % 100 == 0:
            print(f"   Processed {i}/{len(oddswar_teams)} teams...")
    
    print(f"\n📝 Writing to matches.csv...")
    
    with open('matches.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Oddswar', 'Stoiximan', 'Confidence'])
        writer.writeheader()
        writer.writerows(matches)
    
    total_matches = preserved_count + new_match_count
    
    print(f"\n✅ Done!")
    print(f"{'='*60}")
    print(f"📊 Results:")
    print(f"   Total Oddswar teams: {len(oddswar_teams)}")
    print(f"   Total matches: {total_matches}")
    if csv_exists:
        print(f"     - Preserved existing: {preserved_count}")
        print(f"     - New matches found: {new_match_count}")
    else:
        print(f"   Matches found: {total_matches}")
    print(f"   No match: {len(oddswar_teams) - total_matches}")
    print(f"   Match rate: {(total_matches/len(oddswar_teams)*100):.1f}%")
    print(f"\n📄 Output: matches.csv")
    print(f"{'='*60}")


if __name__ == '__main__':
    create_matches_csv()

