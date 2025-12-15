#!/usr/bin/env python3
"""
Create tumbet_matches.csv with Oddswar team names and their probable Tumbet matches.
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
    Remove diacritics/accents from text for comparison purposes only.
    
    Examples:
        Ümraniyespor → Umraniyespor
        Beşiktaş → Besiktas
        Fenerbahçe → Fenerbahce
    
    Returns:
        Normalized text (ASCII, no diacritics)
    """
    # NFD = Canonical Decomposition (separates base char from diacritic)
    nfd = unicodedata.normalize('NFD', text)
    # Filter out combining characters (the diacritics)
    return ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')


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


def find_best_match(oddswar_team, tumbet_teams, threshold=80):
    """
    Find the best matching Tumbet team name for an Oddswar team.
    Uses normalized text (no diacritics) for comparison, but returns original names.
    
    Args:
        oddswar_team: Team name from Oddswar (original with diacritics)
        tumbet_teams: List of team names from Tumbet (original with diacritics)
        threshold: Minimum similarity score (0-100) to consider a match
    
    Returns:
        Tuple of (matched_team, score) or (None, 0) if no good match
        The matched_team returned is the ORIGINAL name with diacritics intact
    """
    if not tumbet_teams:
        return None, 0
    
    # Extract indicators from the Oddswar team name
    oddswar_indicators = extract_indicators(oddswar_team)
    
    # Filter Tumbet teams to only those with matching indicators
    indicator_filtered_teams = [
        t for t in tumbet_teams 
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
    
    # Normalize the Oddswar team name for comparison
    normalized_oddswar = normalize_text(oddswar_team)
    
    # Find best match using normalized names
    result = process.extractOne(
        normalized_oddswar,
        normalized_to_original.keys(),
        scorer=fuzz.ratio
    )
    
    if result and result[1] >= threshold:
        normalized_match = result[0]
        score = result[1]
        # Return the ORIGINAL team name (with diacritics)
        original_match = normalized_to_original[normalized_match]
        return original_match, score
    
    return None, 0


def load_existing_matches():
    """Load existing matches from CSV if it exists."""
    try:
        with open('tumbet_matches.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            existing = {}
            for row in reader:
                oddswar = row['Oddswar'].strip()
                tumbet = row['Tumbet'].strip()
                confidence = row.get('Confidence', '').strip()
                if oddswar:
                    existing[oddswar] = (tumbet, confidence)
            return existing
    except FileNotFoundError:
        return {}


def main():
    print("Loading Oddswar team names (MASTER KEY)...")
    oddswar_teams = load_team_names('oddswar_names.txt')
    print(f"  Loaded {len(oddswar_teams)} Oddswar teams")
    
    print("\nLoading Tumbet team names...")
    tumbet_teams = load_team_names('tumbet_names.txt')
    print(f"  Loaded {len(tumbet_teams)} Tumbet teams")
    
    print("\nLoading existing matches...")
    existing_matches = load_existing_matches()
    print(f"  Found {len(existing_matches)} existing matches")
    
    # Create output CSV
    print("\nMatching teams...")
    matched_count = 0
    new_count = 0
    updated_count = 0
    
    with open('tumbet_matches.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Oddswar', 'Tumbet', 'Confidence'])
        
        for oddswar_team in sorted(oddswar_teams):
            # Check if this team already has a match
            if oddswar_team in existing_matches:
                existing_tumbet, existing_confidence = existing_matches[oddswar_team]
                
                # Skip if already matched (non-empty tumbet, non-zero confidence)
                if existing_tumbet and existing_confidence not in ('', '0.0'):
                    writer.writerow([oddswar_team, existing_tumbet, existing_confidence])
                    matched_count += 1
                    continue
            
            # Find new match
            matched_team, score = find_best_match(oddswar_team, tumbet_teams)
            
            if matched_team:
                writer.writerow([oddswar_team, matched_team, f"{score:.1f}"])
                matched_count += 1
                if oddswar_team not in existing_matches:
                    new_count += 1
                    print(f"  NEW: {oddswar_team} → {matched_team} ({score:.1f})")
                else:
                    updated_count += 1
                    print(f"  UPDATED: {oddswar_team} → {matched_team} ({score:.1f})")
            else:
                writer.writerow([oddswar_team, '', '0.0'])
    
    print(f"\n{'='*60}")
    print(f"Matching complete!")
    print(f"  Total Oddswar teams: {len(oddswar_teams)}")
    print(f"  Matched teams: {matched_count}")
    print(f"  Match rate: {matched_count/len(oddswar_teams)*100:.1f}%")
    print(f"  New matches: {new_count}")
    print(f"  Updated matches: {updated_count}")
    print(f"  Output: tumbet_matches.csv")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()

