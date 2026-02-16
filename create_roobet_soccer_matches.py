#!/usr/bin/env python3
"""
Create roobet_matches.csv with Oddswar team names and their probable Roobet matches.
Uses fuzzy matching (rapidfuzz) to find best matches.
"""

import csv
import re
import unicodedata
from rapidfuzz import fuzz, process


def load_team_names(filename):
    """Load team names from a text file."""
    with open(filename, 'r', encoding='utf-8') as f:
        teams = [line.strip() for line in f if line.strip()]
    return teams


def normalize_text(text):
    """
    Remove diacritics/accents and convert to lowercase for comparison purposes only.
    
    Examples:
        Ümraniyespor → umraniyespor
        Beşiktaş → besiktas
        FENERBAHÇE → fenerbahce
    
    Returns:
        Normalized text (ASCII, lowercase, no diacritics)
    """
    # NFD = Canonical Decomposition (separates base char from diacritic)
    nfd = unicodedata.normalize('NFD', text)
    # Filter out combining characters (the diacritics)
    no_diacritics = ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')
    # Convert to lowercase for case-insensitive comparison
    return no_diacritics.lower()


def extract_indicators(team_name):
    """
    Extract age/gender/reserve indicators from team name.
    
    Returns:
        Set of indicators found (e.g., {'U19', '(W)', 'RESERVE'} or empty set)
    """
    indicators = set()
    
    # Check for age groups: U19, U20, U21, U23
    age_pattern = r'\b(U19|U20|U21|U23)\b'
    age_matches = re.findall(age_pattern, team_name, re.IGNORECASE)
    indicators.update([m.upper() for m in age_matches])
    
    # Check for women's teams: (W)
    if '(W)' in team_name or '(w)' in team_name:
        indicators.add('(W)')
    
    # Check for reserve teams: II or B at the end
    # Both "II" and "B" are treated as equivalent (same indicator)
    # Examples: "Atletico Madrid B", "Atletico Madrid II", "Real Madrid FC B"
    reserve_pattern = r'\s+(II|B)\s*$'
    if re.search(reserve_pattern, team_name):
        indicators.add('RESERVE')
    
    return indicators


def find_best_match(oddswar_team, roobet_teams, threshold=80):
    """
    Find the best matching Roobet team name for an Oddswar team.
    Uses normalized text (no diacritics) for comparison, but returns original names.
    
    Args:
        oddswar_team: Team name from Oddswar (original with diacritics)
        roobet_teams: List of team names from Roobet (original with diacritics)
        threshold: Minimum similarity score (0-100) to consider a match
    
    Returns:
        Tuple of (matched_team, score) or (None, 0) if no good match
        The matched_team returned is the ORIGINAL name with diacritics intact
    """
    if not roobet_teams:
        return None, 0
    
    # Extract indicators from the Oddswar team name
    oddswar_indicators = extract_indicators(oddswar_team)
    
    # Filter Roobet teams to only those with matching indicators
    indicator_filtered_teams = [
        t for t in roobet_teams 
        if extract_indicators(t) == oddswar_indicators
    ]
    
    # If no teams match the indicator criteria, return no match
    if not indicator_filtered_teams:
        return None, 0
    
    # Create mapping: normalized_name → original_name
    # This allows us to compare normalized but return originals
    normalized_to_original = {
        normalize_text(team): team 
        for team in indicator_filtered_teams
    }
    
    # Get list of normalized team names for comparison
    normalized_teams = list(normalized_to_original.keys())
    
    # Compare using normalized text (better for diacritics)
    result = process.extractOne(
        normalize_text(oddswar_team),
        normalized_teams,
        scorer=fuzz.ratio
    )
    
    if result and result[1] >= threshold:
        # Return the ORIGINAL name (with diacritics), not the normalized one
        original_name = normalized_to_original[result[0]]
        return original_name, result[1]
    
    return None, 0


def create_matches_csv():
    """Create roobet_matches.csv with Oddswar and probable Roobet matches."""
    
    print("📂 Loading team names...")
    oddswar_teams = load_team_names('oddswar_names.txt')
    roobet_teams = load_team_names('roobet_names.txt')
    
    print(f"   Oddswar teams: {len(oddswar_teams)}")
    print(f"   Roobet teams: {len(roobet_teams)}")
    
    # Load existing matches if CSV already exists
    existing_matches = {}  # Maps Oddswar -> {'Roobet': name, 'Confidence': score}
    already_used_roobet = set()
    csv_exists = False
    
    try:
        with open('roobet_matches.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                oddswar = row['Oddswar']
                roobet = row.get('Roobet', '')
                confidence = row.get('Confidence', '')
                existing_matches[oddswar] = {
                    'Roobet': roobet,
                    'Confidence': confidence
                }
                if roobet:  # Track already-used Roobet teams
                    already_used_roobet.add(roobet)
        csv_exists = True
        print(f"\n📄 Found existing roobet_matches.csv")
        print(f"   Preserving {len([m for m in existing_matches.values() if m['Roobet']])} existing matches")
        print(f"   {len(already_used_roobet)} Roobet teams already matched")
    except FileNotFoundError:
        print(f"\n📄 No existing roobet_matches.csv found - will create new file")
    
    print("\n🔍 Matching teams (threshold: 80%)...")
    print("   ℹ️  Each Roobet team can only be matched once (prevents duplicates)")
    print("   ℹ️  Preserving existing matches - only filling in blanks")
    print("   ℹ️  Enforcing indicator matching (U19/U20/U21/U23/(W)/II/B must match)")
    print("   ℹ️  Reserve teams: II and B are equivalent (Atletico Madrid II = Atletico Madrid B)")
    print("   ℹ️  Using diacritic-aware matching (Ü=U, ş=s, ç=c, etc.)")
    
    # Track which Roobet teams are available (not already used)
    available_roobet_teams = [t for t in roobet_teams if t not in already_used_roobet]
    print(f"   ℹ️  Available for new matches: {len(available_roobet_teams)} Roobet teams")
    
    matches = []
    new_match_count = 0
    preserved_count = 0
    
    for i, oddswar_team in enumerate(oddswar_teams, 1):
        # Check if this Oddswar team already has a match
        if csv_exists and oddswar_team in existing_matches and existing_matches[oddswar_team]['Roobet']:
            # Preserve existing match AND confidence
            match_data = existing_matches[oddswar_team]
            roobet_match = match_data['Roobet']
            confidence = match_data['Confidence']
            preserved_count += 1
        else:
            # Only search among teams that haven't been matched yet
            roobet_match, score = find_best_match(oddswar_team, available_roobet_teams)
            
            if roobet_match:
                new_match_count += 1
                confidence = f"{score:.1f}"
                if score < 100:  # Show non-exact matches
                    print(f"   [{score:.0f}%] {oddswar_team} → {roobet_match}")
                
                # Remove the matched team from available pool
                available_roobet_teams.remove(roobet_match)
            else:
                roobet_match = None
                confidence = ''
        
        matches.append({
            'Oddswar': oddswar_team,
            'Roobet': roobet_match if roobet_match else '',
            'Confidence': confidence
        })
        
        # Progress indicator
        if i % 100 == 0:
            print(f"   Processed {i}/{len(oddswar_teams)} teams...")
    
    print(f"\n📝 Writing to roobet_matches.csv...")
    
    with open('roobet_matches.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Oddswar', 'Roobet', 'Confidence'])
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
    print(f"\n📄 Output: roobet_matches.csv")
    print(f"{'='*60}")


if __name__ == '__main__':
    create_matches_csv()


