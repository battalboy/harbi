#!/usr/bin/env python3
"""
Create tumbet_matches.csv with Oddswar team names and their probable Tumbet matches.
Uses fuzzy matching (rapidfuzz) to find best matches.

KEY FEATURE: Preserves 100.0 confidence entries (manually validated) even if the Oddswar team
is no longer in oddswar_names.txt. This prevents manual entries from being deleted.
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


def create_matches_csv():
    """
    Create tumbet_matches.csv with Oddswar and probable Tumbet matches.

    PRESERVATION LOGIC:
    - Load existing CSV if it exists
    - Preserve ALL 100.0 confidence entries (manually validated)
    - Only re-match entries that:
      1. Are in oddswar_names.txt (current teams)
      2. Don't have 100.0 confidence (not manually validated)
    - Result: Manual validations are never deleted, even if team disappears from oddswar_names.txt
    """
    
    print("=" * 60)
    print("⚽ Creating Tumbet Soccer Matches CSV")
    print("=" * 60)

    print("\n📂 Loading team names...")
    oddswar_teams = load_team_names('oddswar_names.txt')
    tumbet_teams = load_team_names('tumbet_names.txt')
    
    print(f"   Oddswar teams: {len(oddswar_teams)}")
    print(f"   Tumbet teams: {len(tumbet_teams)}")
    
    # Load existing matches if CSV already exists
    existing_matches = {}
    preserved_100_confidence = {}
    csv_exists = False
    
    try:
        with open('tumbet_matches.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                oddswar = row['Oddswar']
                tumbet = row.get('Tumbet', '')
                confidence = row.get('Confidence', '')
                existing_matches[oddswar] = {
                    'Tumbet': tumbet,
                    'Confidence': confidence
                }
                if confidence == '100.0' and tumbet:
                    preserved_100_confidence[oddswar] = {
                        'Tumbet': tumbet,
                        'Confidence': confidence
                    }
        csv_exists = True
        print(f"\n📄 Found existing tumbet_matches.csv")
        print(f"   Total existing entries: {len(existing_matches)}")
        print(f"   Entries with matches: {len([m for m in existing_matches.values() if m['Tumbet']])}")
        print(f"   🔒 100.0 confidence entries (will be preserved): {len(preserved_100_confidence)}")
    except FileNotFoundError:
        print(f"\n📄 No existing tumbet_matches.csv found - will create new file")
    
    # Create union of teams: oddswar_names.txt + preserved 100.0 entries
    all_oddswar_teams = set(oddswar_teams)
    for oddswar_team in preserved_100_confidence.keys():
        all_oddswar_teams.add(oddswar_team)
    all_oddswar_teams_list = sorted(all_oddswar_teams)
    
    if len(all_oddswar_teams_list) > len(oddswar_teams):
        preserved_count = len(all_oddswar_teams_list) - len(oddswar_teams)
        print(f"   ✅ Including {preserved_count} orphaned 100.0 confidence entries")
    print(f"\n   Final Oddswar team count: {len(all_oddswar_teams_list)}")
    
    print("\n🔍 Matching teams (threshold: 80%)...")
    print("   ℹ️  Each Tumbet team can only be matched once (prevents duplicates)")
    print("   ℹ️  Preserving 100.0 confidence entries (manual validations)")
    print("   ℹ️  Re-matching entries without 100.0 confidence")
    print("   ℹ️  Enforcing indicator matching (U19/U20/U21/U23/(W)/II/B must match)")
    print("   ℹ️  Reserve teams: II and B are equivalent (Atletico Madrid II = Atletico Madrid B)")
    print("   ℹ️  Using diacritic-aware matching (Ü=U, ş=s, ç=c, etc.)")
    
    tumbet_used_by_preserved = set(e['Tumbet'] for e in preserved_100_confidence.values())
    available_tumbet_teams = [t for t in tumbet_teams if t not in tumbet_used_by_preserved]
    print(f"   ℹ️  Tumbet teams reserved by 100.0 entries: {len(tumbet_used_by_preserved)}")
    print(f"   ℹ️  Available for new matches: {len(available_tumbet_teams)} Tumbet teams")
    
    matches = []
    new_match_count = 0
    preserved_100_count = 0
    updated_match_count = 0
    
    for i, oddswar_team in enumerate(all_oddswar_teams_list, 1):
        # Check if this is a preserved 100.0 confidence entry
        if oddswar_team in preserved_100_confidence:
            # ALWAYS preserve 100.0 confidence entries
            match_data = preserved_100_confidence[oddswar_team]
            tumbet_match = match_data['Tumbet']
            confidence = match_data['Confidence']
            preserved_100_count += 1
        # Check if this team is in current oddswar_names.txt
        elif oddswar_team in oddswar_teams:
            # Check if it has an existing non-100.0 match
            if csv_exists and oddswar_team in existing_matches and existing_matches[oddswar_team]['Tumbet']:
                # Has existing match but not 100.0 confidence - we can re-match
                old_match = existing_matches[oddswar_team]['Tumbet']
                old_confidence = existing_matches[oddswar_team]['Confidence']
                # Try to find a better match
                tumbet_match, score = find_best_match(oddswar_team, available_tumbet_teams)
                if tumbet_match:
                    confidence = f"{score:.1f}"
                    updated_match_count += 1
                    if tumbet_match != old_match:
                        print(f"   [UPDATED] {oddswar_team}")
                        print(f"      Old: {old_match} ({old_confidence})")
                        print(f"      New: {tumbet_match} ({confidence})")
                    # Remove from available pool
                    available_tumbet_teams.remove(tumbet_match)
                else:
                    # No match found - leave blank
                    tumbet_match = None
                    confidence = ''
            else:
                # No existing match or blank existing match - search for new match
                tumbet_match, score = find_best_match(oddswar_team, available_tumbet_teams)
                if tumbet_match:
                    new_match_count += 1
                    confidence = f"{score:.1f}"
                    if score < 100:
                        print(f"   [{score:.0f}%] {oddswar_team} → {tumbet_match}")
                    # Remove the matched team from available pool
                    available_tumbet_teams.remove(tumbet_match)
                else:
                    tumbet_match = None
                    confidence = ''
        else:
            # Orphaned entry (not in oddswar_names.txt and not 100.0 confidence)
            tumbet_match = None
            confidence = ''
        
        matches.append({
            'Oddswar': oddswar_team,
            'Tumbet': tumbet_match if tumbet_match else '',
            'Confidence': confidence
        })
        
        # Progress indicator
        if i % 100 == 0:
            print(f"   Processed {i}/{len(all_oddswar_teams_list)} teams...")
    
    print(f"\n📝 Writing to tumbet_matches.csv...")
    
    with open('tumbet_matches.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Oddswar', 'Tumbet', 'Confidence'])
        writer.writeheader()
        writer.writerows(matches)
    
    total_matches = len([m for m in matches if m['Tumbet']])
    
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
    print(f"\n📄 Output: tumbet_matches.csv")
    print(f"{'='*60}")


if __name__ == '__main__':
    create_matches_csv()

