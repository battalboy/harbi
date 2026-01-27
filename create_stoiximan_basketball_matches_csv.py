#!/usr/bin/env python3
"""
Create stoiximan_basketball_matches.csv with Oddswar basketball team names and their probable Stoiximan matches.
Uses fuzzy matching (rapidfuzz) to find best matches.

KEY FEATURE: Preserves 100.0 confidence entries (manually validated) even if the Oddswar team
is no longer in oddswar_basketball_names.txt. This prevents manual entries from being deleted.
"""

import csv
import re
import unicodedata
from rapidfuzz import fuzz, process


def load_team_names(filename):
    """Load team names from a text file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            teams = [line.strip() for line in f if line.strip()]
        return teams
    except FileNotFoundError:
        print(f"⚠️  Warning: {filename} not found, using empty list")
        return []


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


def find_best_match(oddswar_team, stoiximan_teams, threshold=80):
    """
    Find the best matching Stoiximan team name for an Oddswar team.
    Uses normalized text (no diacritics) for comparison, but returns original names.
    
    Args:
        oddswar_team: Team name from Oddswar (original with diacritics)
        stoiximan_teams: List of team names from Stoiximan (original with diacritics)
        threshold: Minimum similarity score (0-100) to consider a match
    
    Returns:
        Tuple of (matched_team, score) or (None, 0) if no good match
        The matched_team returned is the ORIGINAL name with diacritics intact
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
    """
    Create stoiximan_basketball_matches.csv with Oddswar and probable Stoiximan matches.
    
    PRESERVATION LOGIC:
    - Load existing CSV if it exists
    - Preserve ALL 100.0 confidence entries (manually validated)
    - Only re-match entries that:
      1. Are in oddswar_basketball_names.txt (current teams)
      2. Don't have 100.0 confidence (not manually validated)
    - Result: Manual validations are never deleted, even if team disappears from oddswar_basketball_names.txt
    """
    
    print("=" * 60)
    print("🏀 Creating Stoiximan Basketball Matches CSV")
    print("=" * 60)
    
    print("\n📂 Loading team names...")
    oddswar_teams = load_team_names('oddswar_basketball_names.txt')
    stoiximan_teams = load_team_names('stoiximan_basketball_names.txt')
    
    print(f"   Oddswar basketball teams: {len(oddswar_teams)}")
    print(f"   Stoiximan basketball teams: {len(stoiximan_teams)}")
    
    # Load existing matches if CSV already exists
    existing_entries = {}  # Maps Oddswar -> {'Stoiximan': name, 'Confidence': score}
    preserved_100_confidence = {}  # Tracks 100.0 entries to preserve
    already_used_stoiximan = set()
    csv_exists = False
    
    try:
        with open('stoiximan_basketball_matches.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                oddswar = row['Oddswar']
                stoiximan = row.get('Stoiximan', '')
                confidence = row.get('Confidence', '')
                
                existing_entries[oddswar] = {
                    'Stoiximan': stoiximan,
                    'Confidence': confidence
                }
                
                # Track 100.0 confidence entries for preservation
                if confidence == '100.0' and stoiximan:
                    preserved_100_confidence[oddswar] = {
                        'Stoiximan': stoiximan,
                        'Confidence': confidence
                    }
                
                if stoiximan:  # Track already-used Stoiximan teams
                    already_used_stoiximan.add(stoiximan)
        
        csv_exists = True
        print(f"\n📄 Found existing stoiximan_basketball_matches.csv")
        print(f"   Total existing entries: {len(existing_entries)}")
        print(f"   Entries with matches: {len([e for e in existing_entries.values() if e['Stoiximan']])}")
        print(f"   🔒 100.0 confidence entries (will be preserved): {len(preserved_100_confidence)}")
        
    except FileNotFoundError:
        print(f"\n📄 No existing stoiximan_basketball_matches.csv found - will create new file")
    
    # Create union of teams: current oddswar_basketball_names.txt + preserved 100.0 entries
    all_oddswar_teams = set(oddswar_teams)
    for oddswar_team in preserved_100_confidence.keys():
        all_oddswar_teams.add(oddswar_team)
    
    all_oddswar_teams_list = sorted(all_oddswar_teams)
    
    if len(all_oddswar_teams_list) > len(oddswar_teams):
        preserved_count = len(all_oddswar_teams_list) - len(oddswar_teams)
        print(f"   ✅ Including {preserved_count} orphaned 100.0 confidence entries")
    
    print(f"\n   Final Oddswar team count: {len(all_oddswar_teams_list)}")
    
    print("\n🔍 Matching teams (threshold: 80%)...")
    print("   ℹ️  Each Stoiximan team can only be matched once (prevents duplicates)")
    print("   ℹ️  Preserving 100.0 confidence entries (manual validations)")
    print("   ℹ️  Re-matching entries without 100.0 confidence")
    print("   ℹ️  Enforcing indicator matching (U19/U20/U21/U23/(W)/II/B must match)")
    print("   ℹ️  Reserve teams: II and B are equivalent")
    print("   ℹ️  Using diacritic-aware matching (Ü=U, ş=s, ç=c, etc.)")
    
    # Track which Stoiximan teams are available (not already used by 100.0 entries)
    stoiximan_used_by_preserved = set([e['Stoiximan'] for e in preserved_100_confidence.values()])
    available_stoiximan_teams = [t for t in stoiximan_teams if t not in stoiximan_used_by_preserved]
    
    print(f"   ℹ️  Stoiximan teams reserved by 100.0 entries: {len(stoiximan_used_by_preserved)}")
    print(f"   ℹ️  Available for new matches: {len(available_stoiximan_teams)} Stoiximan teams")
    
    matches = []
    new_match_count = 0
    preserved_100_count = 0
    updated_match_count = 0
    
    for i, oddswar_team in enumerate(all_oddswar_teams_list, 1):
        # Check if this is a preserved 100.0 confidence entry
        if oddswar_team in preserved_100_confidence:
            # ALWAYS preserve 100.0 confidence entries
            match_data = preserved_100_confidence[oddswar_team]
            stoiximan_match = match_data['Stoiximan']
            confidence = match_data['Confidence']
            preserved_100_count += 1
            
        # Check if this team is in current oddswar_basketball_names.txt
        elif oddswar_team in oddswar_teams:
            # Check if it has an existing non-100.0 match
            if csv_exists and oddswar_team in existing_entries and existing_entries[oddswar_team]['Stoiximan']:
                # Has existing match but not 100.0 confidence - we can re-match
                old_match = existing_entries[oddswar_team]['Stoiximan']
                old_confidence = existing_entries[oddswar_team]['Confidence']
                
                # Try to find a better match
                stoiximan_match, score = find_best_match(oddswar_team, available_stoiximan_teams)
                
                if stoiximan_match:
                    confidence = f"{score:.1f}"
                    updated_match_count += 1
                    
                    if stoiximan_match != old_match:
                        print(f"   [UPDATED] {oddswar_team}")
                        print(f"      Old: {old_match} ({old_confidence})")
                        print(f"      New: {stoiximan_match} ({confidence})")
                    
                    # Remove from available pool
                    available_stoiximan_teams.remove(stoiximan_match)
                else:
                    # No match found - leave blank
                    stoiximan_match = None
                    confidence = ''
            else:
                # No existing match or blank existing match - search for new match
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
        else:
            # Orphaned entry (not in oddswar_basketball_names.txt and not 100.0 confidence)
            # This shouldn't happen with our logic, but just in case
            stoiximan_match = None
            confidence = ''
        
        matches.append({
            'Oddswar': oddswar_team,
            'Stoiximan': stoiximan_match if stoiximan_match else '',
            'Confidence': confidence
        })
        
        # Progress indicator
        if i % 50 == 0:
            print(f"   Processed {i}/{len(all_oddswar_teams_list)} teams...")
    
    print(f"\n📝 Writing to stoiximan_basketball_matches.csv...")
    
    with open('stoiximan_basketball_matches.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Oddswar', 'Stoiximan', 'Confidence'])
        writer.writeheader()
        writer.writerows(matches)
    
    total_matches = len([m for m in matches if m['Stoiximan']])
    
    print(f"\n✅ Done!")
    print(f"{'='*60}")
    print(f"📊 Results:")
    print(f"   Total Oddswar teams: {len(all_oddswar_teams_list)}")
    print(f"   Total matches: {total_matches}")
    if csv_exists:
        print(f"     - 🔒 Preserved 100.0 confidence: {preserved_100_count}")
        print(f"     - 🔄 Updated existing matches: {updated_match_count}")
        print(f"     - ✨ New matches found: {new_match_count}")
    else:
        print(f"   Matches found: {total_matches}")
    print(f"   No match: {len(all_oddswar_teams_list) - total_matches}")
    print(f"   Match rate: {(total_matches/len(all_oddswar_teams_list)*100):.1f}%")
    print(f"\n📄 Output: stoiximan_basketball_matches.csv")
    print(f"{'='*60}")


if __name__ == '__main__':
    create_matches_csv()
