#!/usr/bin/env python3
"""
Stoiximan Basketball Team Name Collector (COMPREHENSIVE)

Fetches Stoiximan basketball matches from ALL available leagues worldwide.
Uses the /api/sport/basketball/competitions/ endpoint with dropdown discovery.

This is a ONE-TIME comprehensive fetch (not continuous collection).
Output: stoiximan_basketball_names.txt (one team name per line, sorted, no duplicates)

Note: Requires VPN connected to Greek IP address.
"""

import cloudscraper
import time
import platform
from typing import Set, List, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


# Configuration
OUTPUT_FILE = 'stoiximan_basketball_names.txt'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://en.stoiximan.gr/sport/basketball/'
}

# Proxy configuration (only used on Linux remote server)
def get_proxies():
    """Return proxy configuration if on Linux (remote server), None if macOS (local)."""
    if platform.system() == 'Linux':
        # Remote server - use Gluetun Greece proxy
        return {
            'http': 'http://127.0.0.1:8888',
            'https': 'http://127.0.0.1:8888'
        }
    else:
        # macOS - using system-wide ExpressVPN
        return None


def discover_all_leagues() -> List[Tuple[str, str, str, str]]:
    """
    Fetch dropdown list to discover all available basketball leagues.
    
    Returns:
        List of tuples: (region_name, region_id, league_id, display_name)
    """
    print("🔍 Discovering all basketball leagues...")
    
    # Use a sample region to fetch the dropdown list (contains ALL leagues globally)
    url = 'https://en.stoiximan.gr/api/sport/basketball/competitions/greece/10021/?req=la,s,stnf,c,mb'
    
    proxies = get_proxies()
    scraper = cloudscraper.create_scraper()
    
    try:
        response = scraper.get(url, headers=HEADERS, proxies=proxies, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Failed to fetch dropdown: HTTP {response.status_code}")
            return []
        
        data = response.json()
        
        if 'data' not in data or 'dropdownList' not in data['data']:
            print(f"❌ Invalid response structure")
            return []
        
        dropdown = data['data']['dropdownList']
        print(f"✅ Found {len(dropdown)} regions with basketball leagues\n")
        
        # Extract all region/league combinations
        all_leagues = []
        
        for region in dropdown:
            region_id = region.get('id')
            region_name_display = region.get('name')
            region_url = region.get('url', '')
            
            # Extract region name from URL (e.g., /sport/basketball/competitions/greece/10021/)
            region_name = region_url.split('/')[4] if len(region_url.split('/')) > 4 else region_name_display.lower().replace(' ', '-')
            
            leagues = region.get('leagues', [])
            
            for league in leagues:
                league_id = league.get('id')
                league_name = league.get('text')
                
                display_name = f"{region_name_display} - {league_name}"
                all_leagues.append((region_name, region_id, league_id, display_name))
        
        print(f"📊 Total leagues to fetch: {len(all_leagues)}\n")
        return all_leagues
    
    except Exception as e:
        print(f"❌ Error discovering leagues: {e}")
        return []


def fetch_teams_from_league(league_info: Tuple[str, str, str, str], scraper, proxies) -> Set[str]:
    """
    Fetch team names from a specific league.
    
    Args:
        league_info: Tuple of (region_name, region_id, league_id, display_name)
        scraper: cloudscraper instance
        proxies: proxy configuration
    
    Returns:
        Set of team names
    """
    region_name, region_id, league_id, display_name = league_info
    url = f'https://en.stoiximan.gr/api/sport/basketball/competitions/{region_name}/{region_id}/?sl={league_id}&req=la,s,stnf,c,mb'
    
    try:
        response = scraper.get(url, headers=HEADERS, proxies=proxies, timeout=15)
        
        if response.status_code != 200:
            return set()
        
        data = response.json()
        
        if 'data' not in data or 'blocks' not in data['data']:
            return set()
        
        teams = set()
        blocks = data['data']['blocks']
        
        for block in blocks:
            events = block.get('events', [])
            
            for event in events:
                participants = event.get('participants', [])
                
                if len(participants) < 2:
                    continue
                
                team1 = participants[0].get('name', '')
                team2 = participants[1].get('name', '')
                
                # Skip esports/virtual matches
                esports_keywords = ['(Esports)', '(esports)', '(E)']
                virtual_tournaments = ['(GODFATHER)', '(KJMR)', '(RIDER)', '(CARNAGE)', 
                                      '(CRYPTO)', '(ARCHER)', '(mist)', '(RAMZ)']
                
                skip_team1 = any(keyword in team1 for keyword in esports_keywords + virtual_tournaments)
                skip_team2 = any(keyword in team2 for keyword in esports_keywords + virtual_tournaments)
                
                if skip_team1 or skip_team2:
                    continue
                
                # Skip tournament outright betting markets (continent/region vs generic groups)
                generic_regions = ['Europe', 'USA', 'Asia', 'Africa', 'Americas']
                group_pattern = any(
                    name.startswith('Group ') and len(name) == 7  # "Group A", "Group B", etc.
                    for name in [team1, team2]
                )
                continent = any(
                    name in generic_regions
                    for name in [team1, team2]
                )
                if group_pattern or (continent and group_pattern):
                    continue
                
                if team1:
                    teams.add(team1)
                if team2:
                    teams.add(team2)
        
        return teams
    
    except Exception as e:
        return set()


def save_teams(teams: Set[str]):
    """Save team names to file (sorted, one per line)."""
    sorted_teams = sorted(teams)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for team in sorted_teams:
            f.write(team + '\n')


def main():
    """Main collection function."""
    print("=" * 70)
    print("🏀 Stoiximan Basketball Team Name Collector (COMPREHENSIVE)")
    print("=" * 70)
    print(f"📝 Output file: {OUTPUT_FILE}")
    print(f"🇬🇷 Requires VPN connected to Greek IP")
    
    proxies = get_proxies()
    env_info = "🔌 Using Gluetun proxy (127.0.0.1:8888)" if proxies else "🌐 Using system-wide VPN"
    print(f"{env_info}\n")
    
    # Discover all leagues
    start_time = datetime.now()
    all_leagues = discover_all_leagues()
    
    if not all_leagues:
        print("❌ Failed to discover leagues. Exiting.")
        return
    
    # Fetch teams from all leagues in parallel
    scraper = cloudscraper.create_scraper()
    all_teams = set()
    leagues_with_matches = 0
    
    print("🔄 Fetching teams from all leagues (parallel)...")
    print("=" * 70)
    
    # Use ThreadPoolExecutor for parallel fetching (10 workers)
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Submit all fetch tasks
        future_to_league = {
            executor.submit(fetch_teams_from_league, league_info, scraper, proxies): league_info 
            for league_info in all_leagues
        }
        
        # Collect results as they complete
        completed = 0
        for future in as_completed(future_to_league):
            completed += 1
            league_info = future_to_league[future]
            display_name = league_info[3]
            
            print(f"[{completed}/{len(all_leagues)}] {display_name[:50]:<50}", end=" ", flush=True)
            
            try:
                teams = future.result()
                if teams:
                    all_teams.update(teams)
                    leagues_with_matches += 1
                    print(f"✅ {len(teams)} teams")
                else:
                    print("⚠️  0 matches")
            except Exception:
                print("❌ Error")
    
    # Save results
    save_teams(all_teams)
    
    # Summary
    elapsed = (datetime.now() - start_time).total_seconds()
    print("=" * 70)
    print(f"\n✅ COLLECTION COMPLETE!")
    print(f"📊 Unique teams collected: {len(all_teams)}")
    print(f"🏆 Leagues with matches: {leagues_with_matches}/{len(all_leagues)}")
    print(f"⏱️  Time elapsed: {elapsed:.1f} seconds")
    print(f"💾 Saved to: {OUTPUT_FILE}\n")


if __name__ == '__main__':
    main()
