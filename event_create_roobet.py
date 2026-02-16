"""
Roobet Live Soccer Match Parser

This script fetches live and prematch soccer matches from Roobet's API (Betsby) and extracts:
- Team names
- Match odds (1X2 - Team 1 Win, Draw, Team 2 Win)
- Match links

Output is formatted identically to stoiximan-formatted.txt and oddswar-formatted.txt for easy comparison.
"""

import json
import requests
from datetime import datetime, timezone
from typing import List, Dict, Optional
from error_handler import handle_request_error, success_response, is_ban_indicator


# Configuration
SITE_NAME = 'Roobet'
OUTPUT_FILE = 'roobet-formatted.txt'
ERROR_LOG_FILE = 'roobet-error.json'
BRAND_ID = '2186449803775455232'
BASE_URL = 'https://api-g-c7818b61-607.sptpub.com'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Origin': 'https://roobet.com',
    'Referer': 'https://roobet.com/sports/soccer-1'
}


def extract_categories_and_tournaments_from_data(data: Dict) -> tuple:
    """
    Extract category and tournament mappings from the prematch data response.
    
    Args:
        data: Prematch API response containing categories and tournaments
    
    Returns:
        tuple: (categories_dict, tournaments_dict, tournament_names_dict) where:
            - categories_dict: {category_id: category_slug}
            - tournaments_dict: {tournament_id: tournament_slug}
            - tournament_names_dict: {tournament_id: tournament_display_name}
    """
    categories = {}
    tournaments = {}
    tournament_names = {}
    
    try:
        # Extract categories from response
        if 'categories' in data:
            for cat_id, cat_data in data['categories'].items():
                # Only include soccer (sport_id = '1')
                if cat_data.get('sport_id') == '1':
                    slug = cat_data.get('slug', cat_data.get('name', ''))
                    if slug:
                        categories[cat_id] = slug
        
        # Extract tournaments from response
        if 'tournaments' in data:
            for tour_id, tour_data in data['tournaments'].items():
                slug = tour_data.get('slug', tour_data.get('name', ''))
                name = tour_data.get('name', slug)
                if slug:
                    tournaments[tour_id] = slug
                    tournament_names[tour_id] = name
                    
    except Exception as e:
        print(f"Warning: Error extracting categories/tournaments: {e}")
    
    return categories, tournaments, tournament_names


def fetch_events_data(endpoint_type='live') -> Optional[Dict]:
    """
    Fetch events data using Betsby API two-step process.
    
    For prematch, this fetches from ALL version endpoints:
    - main version
    - top_events_versions
    - rest_events_versions
    
    Args:
        endpoint_type: 'live' or 'prematch'
    
    Returns:
        Dict with 'events', and for prematch also 'categories' and 'tournaments', or None on error
    """
    try:
        # Step 1: Get version manifest
        manifest_url = f"{BASE_URL}/api/v4/{endpoint_type}/brand/{BRAND_ID}/en/0"
        response = requests.get(manifest_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        manifest = response.json()
        
        # Get all versions to fetch
        main_version = manifest.get('version')
        if not main_version:
            print(f"Warning: No version found in {endpoint_type} manifest")
            return None
        
        # For prematch, also get top_events_versions and rest_events_versions
        versions_to_fetch = [main_version]
        if endpoint_type == 'prematch':
            top_versions = manifest.get('top_events_versions', [])
            rest_versions = manifest.get('rest_events_versions', [])
            versions_to_fetch.extend(top_versions)
            versions_to_fetch.extend(rest_versions)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_versions = []
        for v in versions_to_fetch:
            if v not in seen:
                seen.add(v)
                unique_versions.append(v)
        
        # Step 2: Fetch data from all versions and combine
        combined_events = {}
        categories = {}
        tournaments = {}
        
        for idx, version in enumerate(unique_versions):
            events_url = f"{BASE_URL}/api/v4/{endpoint_type}/brand/{BRAND_ID}/en/{version}"
            response = requests.get(events_url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Merge events from this version
            if 'events' in data:
                combined_events.update(data['events'])
            
            # For prematch, merge categories and tournaments from ALL versions
            # (each version may have different tournaments not in the main version)
            if endpoint_type == 'prematch':
                if 'categories' in data:
                    categories.update(data['categories'])
                if 'tournaments' in data:
                    tournaments.update(data['tournaments'])
        
        if combined_events:
            result = {'events': combined_events}
            # Add categories and tournaments for prematch
            if endpoint_type == 'prematch':
                result['categories'] = categories
                result['tournaments'] = tournaments
            return result
        
        return None
        
    except requests.RequestException as e:
        print(f"Error fetching {endpoint_type} data: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error in {endpoint_type}: {e}")
        return None


def extract_1x2_odds(event: Dict) -> tuple:
    """
    Extract 1X2 odds from event data.
    
    Betsby API structure:
    markets: {
        "1": {  # Market ID 1 is 1X2
            "": {
                "1": {"k": "1.42"},  # Home win
                "2": {"k": "4.2"},   # Draw
                "3": {"k": "6.4"}    # Away win
            }
        }
    }
    
    Returns:
        tuple: (team1_odds, draw_odds, team2_odds) or (None, None, None)
    """
    team1_odds = None
    draw_odds = None
    team2_odds = None
    
    # Look for markets in the event
    markets = event.get('markets', {})
    
    # Market ID "1" is the 1X2 market in Betsby API
    if '1' in markets:
        market_1x2 = markets['1']
        
        # Get the selections (usually under "" key)
        selections = market_1x2.get('', {})
        
        # Selection IDs: "1" = Home, "2" = Draw, "3" = Away
        if '1' in selections:
            team1_odds = selections['1'].get('k')
        if '2' in selections:
            draw_odds = selections['2'].get('k')
        if '3' in selections:
            team2_odds = selections['3'].get('k')
    
    return team1_odds, draw_odds, team2_odds


def parse_matches(data: Dict, endpoint_type: str = 'live', categories: Dict = None, tournaments: Dict = None, tournament_names: Dict = None) -> List[Dict]:
    """
    Parse match data from Betsby API response and extract match information.
    
    Args:
        data: Response from Betsby API
        endpoint_type: 'live' or 'prematch' (for URL construction)
        categories: Dict mapping category IDs to slugs
        tournaments: Dict mapping tournament IDs to slugs
        tournament_names: Dict mapping tournament IDs to display names
    
    Returns:
        List of match dictionaries with team names, odds, and links
    """
    matches = []
    
    if not data or not isinstance(data, dict):
        return matches
    
    # Use empty dicts if not provided
    if categories is None:
        categories = {}
    if tournaments is None:
        tournaments = {}
    if tournament_names is None:
        tournament_names = {}
    
    # Betsby API structure: events[event_id]
    events = data.get('events', {})
    
    for event_id, event in events.items():
        try:
            desc = event.get('desc', {})
            
            # Filter for soccer only (sport_id = '1')
            if desc.get('sport') != '1':
                continue
            
            # Get competitors
            competitors = desc.get('competitors', [])
            if len(competitors) < 2:
                continue
            
            team1_name = competitors[0].get('name', 'Unknown')
            team2_name = competitors[1].get('name', 'Unknown')
            
            # Extract 1X2 odds
            team1_odds, draw_odds, team2_odds = extract_1x2_odds(event)
            
            # Build match URL with full path
            # Roobet URL format: https://roobet.com/sports/soccer/{category_slug}/{tournament_slug}/{event_slug}-{event_id}
            slug = desc.get('slug', '')
            category_id = desc.get('category', '')
            tournament_id = desc.get('tournament', '')
            
            # Get slugs from mappings
            category_slug = categories.get(category_id, category_id)
            tournament_slug = tournaments.get(tournament_id, tournament_id)
            
            # Construct full URL
            if slug and category_slug and tournament_slug:
                match_url = f"https://roobet.com/sports/soccer/{category_slug}/{tournament_slug}/{slug}-{event_id}"
            elif slug:
                # Fallback to shorter URL if we don't have category/tournament
                match_url = f"https://roobet.com/sports/{slug}-{event_id}"
            else:
                # Last resort fallback
                match_url = f"https://roobet.com/sports/event/{event_id}"
            
            # Get scheduled timestamp (Unix seconds) and convert to ISO 8601
            scheduled = desc.get('scheduled', 0)
            if scheduled:
                try:
                    start_time = datetime.fromtimestamp(scheduled, tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')
                except (ValueError, OSError):
                    start_time = 'N/A'
            else:
                start_time = 'N/A'
            
            status = 'Canlı Maç' if endpoint_type == 'live' else 'Gelen Maç'
            league = tournament_names.get(tournament_id, 'N/A')
            
            match = {
                'id': event_id,
                'team1': team1_name,
                'team2': team2_name,
                'team1_odds': team1_odds if team1_odds else 'N/A',
                'draw_odds': draw_odds if draw_odds else 'N/A',
                'team2_odds': team2_odds if team2_odds else 'N/A',
                'competition': league,
                'url': match_url,
                'is_live': endpoint_type == 'live',
                'status': status,
                'start_time': start_time
            }
            
            matches.append(match)
            
        except Exception as e:
            print(f"Error parsing event {event_id}: {e}", flush=True)
            continue
    
    return matches


def format_match(match: Dict) -> str:
    """
    Format a match dictionary into a human-readable string.
    Includes Status, League, and Start Time (aligned with oddswar-formatted.txt).
    
    Args:
        match: A dictionary containing match data
    
    Returns:
        str: A formatted string representing the match
    """
    team1 = match.get('team1', 'N/A')
    team2 = match.get('team2', 'N/A')
    team1_odds = match.get('team1_odds', 'N/A')
    draw_odds = match.get('draw_odds', 'N/A')
    team2_odds = match.get('team2_odds', 'N/A')
    link_url = match.get('url', 'N/A')
    status = match.get('status', 'Gelen Maç')
    league = match.get('competition', 'N/A')
    start_time = match.get('start_time', 'N/A')
    
    return (
        f"Team 1: {team1} | Team 2: {team2} | "
        f"Team 1 Win: {team1_odds} | Draw: {draw_odds} | Team 2 Win: {team2_odds} | "
        f"Link: {link_url} | Status: {status} | League: {league} | Start Time: {start_time}"
    )


def save_formatted_matches(matches: List[Dict], output_file: str = 'roobet-formatted.txt'):
    """
    Save formatted matches to a text file.
    File is overwritten each time to ensure only latest data.
    
    Args:
        matches: List of match dictionaries
        output_file: Output filename
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        for match in matches:
            f.write(format_match(match) + '\n')
    
    print(f"\n✅ Saved {len(matches)} matches to {output_file}")


def main():
    """Main execution function with comprehensive error handling."""
    try:
        print(f"Fetching {SITE_NAME} live and prematch soccer matches...")
        
        all_matches = []
        categories = {}
        tournaments = {}
        tournament_names = {}
        
        # Step 1: Fetch PREMATCH matches (this includes categories/tournaments metadata)
        print("\n1. Fetching PREMATCH matches...")
        prematch_data = fetch_events_data('prematch')
        if prematch_data:
            # Extract categories and tournaments from the prematch data
            categories, tournaments, tournament_names = extract_categories_and_tournaments_from_data(prematch_data)
            print(f"   Found {len(categories)} soccer categories and {len(tournaments)} tournaments")
            
            prematch_matches = parse_matches(prematch_data, 'prematch', categories, tournaments, tournament_names)
            all_matches.extend(prematch_matches)
            print(f"   Found {len(prematch_matches)} prematch matches")
        else:
            print("   No prematch matches found")
        
        # Step 2: Fetch LIVE matches (use categories/tournaments from prematch)
        print("\n2. Fetching LIVE matches...")
        live_data = fetch_events_data('live')
        if live_data:
            live_matches = parse_matches(live_data, 'live', categories, tournaments, tournament_names)
            all_matches.extend(live_matches)
            print(f"   Found {len(live_matches)} live matches")
        else:
            print("   No live matches found")
        
        # Step 3: Report statistics
        print(f"\n3. Processing results...")
        matches_with_odds = [m for m in all_matches if m['team1_odds'] != 'N/A']
        print(f"   Total matches: {len(all_matches)}")
        print(f"   Matches with 1X2 odds: {len(matches_with_odds)}")
        print(f"   Matches missing odds: {len(all_matches) - len(matches_with_odds)}")
        
        # Step 4: Save to file
        if all_matches:
            print("\n4. Saving formatted output...")
            save_formatted_matches(all_matches)
            
            # Write success status
            success_info = success_response(SITE_NAME)
            with open(ERROR_LOG_FILE, 'w', encoding='utf-8') as f:
                json.dump(success_info, f, ensure_ascii=False, indent=2)
            
            print("\n✨ Done!")
            return success_info
        else:
            print("\n⚠️  No matches found!")
            # Write empty output file
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                f.write('')
            # Write NoEventsFound status
            error_info = handle_request_error(SITE_NAME, Exception("NoEventsFound"))
            with open(ERROR_LOG_FILE, 'w', encoding='utf-8') as f:
                json.dump(error_info, f, ensure_ascii=False, indent=2)
            return error_info
        
    except requests.exceptions.HTTPError as e:
        # HTTP error with status code
        status_code = e.response.status_code if (e.response is not None) else None
        error_info = handle_request_error(SITE_NAME, e, status_code)
        
        print(f"\n❌ HTTP Error {status_code}: {error_info['error_message']}")
        
        # Check for ban indicators
        if is_ban_indicator(error_info['error_type'], status_code):
            print(f"\n⚠️  WARNING: Possible IP ban detected for {SITE_NAME}!")
            print(f"   Consider stopping all requests and waiting before retrying.")
        
        # Write error log and empty output
        with open(ERROR_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(error_info, f, ensure_ascii=False, indent=2)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write('')
        
        return error_info
        
    except requests.exceptions.ConnectionError as e:
        error_info = handle_request_error(SITE_NAME, e)
        print(f"\n❌ Connection Error: {error_info['error_message']}")
        
        with open(ERROR_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(error_info, f, ensure_ascii=False, indent=2)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write('')
        
        return error_info
        
    except requests.exceptions.Timeout as e:
        error_info = handle_request_error(SITE_NAME, e)
        print(f"\n❌ Timeout Error: {error_info['error_message']}")
        
        with open(ERROR_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(error_info, f, ensure_ascii=False, indent=2)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write('')
        
        return error_info
        
    except json.JSONDecodeError as e:
        error_info = handle_request_error(SITE_NAME, e)
        print(f"\n❌ JSON Parse Error: {error_info['error_message']}")
        
        with open(ERROR_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(error_info, f, ensure_ascii=False, indent=2)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write('')
        
        return error_info
        
    except Exception as e:
        error_info = handle_request_error(SITE_NAME, e)
        print(f"\n❌ Unexpected Error: {error_info['error_message']}")
        print(f"   Technical details: {str(e)}")
        
        with open(ERROR_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(error_info, f, ensure_ascii=False, indent=2)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write('')
        
        return error_info


if __name__ == '__main__':
    result = main()
    # Exit with error code if there was an error
    if result and result.get('error', False):
        exit(1)
    else:
        exit(0)

