#!/usr/bin/env python3
"""
Arbitrage Opportunity Detector

Matches events across Oddswar (exchange) and traditional bookmakers
(Roobet, Stoiximan, Tumbet) to identify potential arbitrage opportunities.

Uses team name mappings from CSV files and event data from formatted text files.
"""

import csv
from typing import Dict, List, Tuple, Optional
from pathlib import Path


def load_team_mappings(csv_file: str) -> Dict[str, str]:
    """
    Load team mappings from CSV file.
    Returns dict: {oddswar_name: traditional_site_name}
    Only includes rows with non-blank confidence scores.
    """
    mappings = {}
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        
        for row in reader:
            if len(row) >= 3:
                oddswar_team = row[0].strip()
                traditional_team = row[1].strip()
                confidence = row[2].strip()
                
                # Only include if there's a match (non-blank traditional team and confidence)
                if traditional_team and confidence:
                    mappings[oddswar_team] = traditional_team
    
    return mappings


def parse_formatted_file(file_path: str) -> Dict[Tuple[str, str], Dict]:
    """
    Parse formatted event file (pipe-separated format).
    Returns dict: {(team1, team2): {odds_1, odds_x, odds_2, link}}
    """
    events = {}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            # Parse: Team 1: X | Team 2: Y | Team 1 Win: Z | Draw: Z | Team 2 Win: Z | Link: URL
            parts = [p.strip() for p in line.split('|')]
            
            if len(parts) < 6:
                continue
            
            try:
                team1 = parts[0].split(':', 1)[1].strip()
                team2 = parts[1].split(':', 1)[1].strip()
                odds_1 = parts[2].split(':', 1)[1].strip()
                odds_x = parts[3].split(':', 1)[1].strip()
                odds_2 = parts[4].split(':', 1)[1].strip()
                link = parts[5].split(':', 1)[1].strip()
                
                # Skip if any odds are N/A
                if odds_1 == 'N/A' or odds_x == 'N/A' or odds_2 == 'N/A':
                    continue
                
                events[(team1, team2)] = {
                    'odds_1': odds_1,
                    'odds_x': odds_x,
                    'odds_2': odds_2,
                    'link': link
                }
            except (IndexError, ValueError):
                continue
    
    return events


def find_matching_events(
    oddswar_events: Dict[Tuple[str, str], Dict],
    traditional_events: Dict[Tuple[str, str], Dict],
    oddswar_to_traditional: Dict[str, str]
) -> Dict[Tuple[str, str], Dict]:
    """
    Find events that exist in both Oddswar and a traditional site.
    
    Args:
        oddswar_events: Oddswar events dict
        traditional_events: Traditional site events dict
        oddswar_to_traditional: Team name mapping dict
    
    Returns:
        Dict of matched events: {(oddswar_team1, oddswar_team2): traditional_event_data}
    """
    matches = {}
    
    for (oddswar_team1, oddswar_team2), oddswar_data in oddswar_events.items():
        # Check if both teams have mappings
        if oddswar_team1 not in oddswar_to_traditional:
            continue
        if oddswar_team2 not in oddswar_to_traditional:
            continue
        
        # Get traditional site team names
        trad_team1 = oddswar_to_traditional[oddswar_team1]
        trad_team2 = oddswar_to_traditional[oddswar_team2]
        
        # Check if this event exists in traditional site (exact order only)
        if (trad_team1, trad_team2) in traditional_events:
            matches[(oddswar_team1, oddswar_team2)] = traditional_events[(trad_team1, trad_team2)]
    
    return matches


def generate_html(matched_events: List[Dict], output_file: str = 'results.html'):
    """
    Generate HTML file with matched events in table format.
    
    Args:
        matched_events: List of dicts containing event data and matches
        output_file: Path to output HTML file
    """
    
    # HTML header
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Harbi - Arbitrage Results</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        
        .event-table {
            width: 80%;
            margin: 20px auto;
            border-collapse: collapse;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .event-table th {
            background-color: #e0e0e0;
            padding: 10px;
            text-align: center;
            border: 1px solid #ccc;
        }
        
        .event-table td {
            padding: 10px;
            text-align: center;
            border: 1px solid #ccc;
        }
        
        .site-name {
            font-weight: bold;
            text-align: left;
        }
        
        .header-row {
            background-color: #d0d0d0;
            font-size: 1.1em;
        }
        
        .arb-opportunity {
            background-color: #dc3545;
            color: white;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <h1 style="text-align: center;">H.Ar.B.İ. - Arbitrage Oran Sonuçları</h1>
"""
    
    # Add event tables
    for event in matched_events:
        team1 = event['team1']
        team2 = event['team2']
        oddswar = event['oddswar']
        
        # Start table
        html += f"""
    <!-- Event: {team1} vs {team2} -->
    <table class="event-table">
        <thead>
            <tr class="header-row">
                <th colspan="4">{team1} VS {team2}</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td class="site-name"><a href="{oddswar['link']}" target="_blank">Oddswar oranları</a></td>
                <td>{oddswar['odds_1']}</td>
                <td>{oddswar['odds_x']}</td>
                <td>{oddswar['odds_2']}</td>
            </tr>
"""
        
        # Add Tumbet row if matched
        if 'tumbet' in event:
            tumbet = event['tumbet']
            # Compare odds and highlight arbitrage opportunities
            try:
                odds_1_class = ' class="arb-opportunity"' if float(tumbet['odds_1']) > float(oddswar['odds_1']) else ''
                odds_x_class = ' class="arb-opportunity"' if float(tumbet['odds_x']) > float(oddswar['odds_x']) else ''
                odds_2_class = ' class="arb-opportunity"' if float(tumbet['odds_2']) > float(oddswar['odds_2']) else ''
            except (ValueError, KeyError):
                odds_1_class = odds_x_class = odds_2_class = ''
            
            html += f"""            <tr>
                <td class="site-name"><a href="{tumbet['link']}" target="_blank">Tumbet oranları</a></td>
                <td{odds_1_class}>{tumbet['odds_1']}</td>
                <td{odds_x_class}>{tumbet['odds_x']}</td>
                <td{odds_2_class}>{tumbet['odds_2']}</td>
            </tr>
"""
        
        # Add Stoiximan row if matched
        if 'stoiximan' in event:
            stoiximan = event['stoiximan']
            # Compare odds and highlight arbitrage opportunities
            try:
                odds_1_class = ' class="arb-opportunity"' if float(stoiximan['odds_1']) > float(oddswar['odds_1']) else ''
                odds_x_class = ' class="arb-opportunity"' if float(stoiximan['odds_x']) > float(oddswar['odds_x']) else ''
                odds_2_class = ' class="arb-opportunity"' if float(stoiximan['odds_2']) > float(oddswar['odds_2']) else ''
            except (ValueError, KeyError):
                odds_1_class = odds_x_class = odds_2_class = ''
            
            html += f"""            <tr>
                <td class="site-name"><a href="{stoiximan['link']}" target="_blank">Stoiximan oranları</a></td>
                <td{odds_1_class}>{stoiximan['odds_1']}</td>
                <td{odds_x_class}>{stoiximan['odds_x']}</td>
                <td{odds_2_class}>{stoiximan['odds_2']}</td>
            </tr>
"""
        
        # Add Roobet row if matched
        if 'roobet' in event:
            roobet = event['roobet']
            # Compare odds and highlight arbitrage opportunities
            try:
                odds_1_class = ' class="arb-opportunity"' if float(roobet['odds_1']) > float(oddswar['odds_1']) else ''
                odds_x_class = ' class="arb-opportunity"' if float(roobet['odds_x']) > float(oddswar['odds_x']) else ''
                odds_2_class = ' class="arb-opportunity"' if float(roobet['odds_2']) > float(oddswar['odds_2']) else ''
            except (ValueError, KeyError):
                odds_1_class = odds_x_class = odds_2_class = ''
            
            html += f"""            <tr>
                <td class="site-name"><a href="{roobet['link']}" target="_blank">Roobet oranları</a></td>
                <td{odds_1_class}>{roobet['odds_1']}</td>
                <td{odds_x_class}>{roobet['odds_x']}</td>
                <td{odds_2_class}>{roobet['odds_2']}</td>
            </tr>
"""
        
        # Close table
        html += """        </tbody>
    </table>
"""
    
    # HTML footer
    html += """
</body>
</html>
"""
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)


def main():
    print("="*80)
    print("HARBI - ARBITRAGE OPPORTUNITY DETECTOR")
    print("="*80)
    
    # Step 1: Load team mappings
    print("\n📂 Loading team mappings...")
    oddswar_to_roobet = load_team_mappings('roobet_matches.csv')
    oddswar_to_stoiximan = load_team_mappings('stoiximan_matches.csv')
    oddswar_to_tumbet = load_team_mappings('tumbet_matches.csv')
    
    print(f"   ✅ Roobet: {len(oddswar_to_roobet)} team mappings")
    print(f"   ✅ Stoiximan: {len(oddswar_to_stoiximan)} team mappings")
    print(f"   ✅ Tumbet: {len(oddswar_to_tumbet)} team mappings")
    
    # Step 2: Load events
    print("\n📂 Loading events from formatted files...")
    oddswar_events = parse_formatted_file('oddswar-formatted.txt')
    roobet_events = parse_formatted_file('roobet-formatted.txt')
    stoiximan_events = parse_formatted_file('stoiximan-formatted.txt')
    tumbet_events = parse_formatted_file('tumbet-formatted.txt')
    
    print(f"   ✅ Oddswar: {len(oddswar_events)} events")
    print(f"   ✅ Roobet: {len(roobet_events)} events")
    print(f"   ✅ Stoiximan: {len(stoiximan_events)} events")
    print(f"   ✅ Tumbet: {len(tumbet_events)} events")
    
    # Step 3: Find matching events
    print("\n🔍 Matching events across sites...")
    roobet_matches = find_matching_events(oddswar_events, roobet_events, oddswar_to_roobet)
    stoiximan_matches = find_matching_events(oddswar_events, stoiximan_events, oddswar_to_stoiximan)
    tumbet_matches = find_matching_events(oddswar_events, tumbet_events, oddswar_to_tumbet)
    
    print(f"   ✅ Roobet: {len(roobet_matches)} matching events")
    print(f"   ✅ Stoiximan: {len(stoiximan_matches)} matching events")
    print(f"   ✅ Tumbet: {len(tumbet_matches)} matching events")
    
    # Step 4: Consolidate results
    print("\n🔧 Consolidating results...")
    matched_events = []
    
    for (team1, team2), oddswar_data in oddswar_events.items():
        event = {
            'team1': team1,
            'team2': team2,
            'oddswar': oddswar_data
        }
        
        # Check if this event matched on any traditional site
        has_matches = False
        
        if (team1, team2) in roobet_matches:
            event['roobet'] = roobet_matches[(team1, team2)]
            has_matches = True
        
        if (team1, team2) in stoiximan_matches:
            event['stoiximan'] = stoiximan_matches[(team1, team2)]
            has_matches = True
        
        if (team1, team2) in tumbet_matches:
            event['tumbet'] = tumbet_matches[(team1, team2)]
            has_matches = True
        
        # Only include if at least one traditional site matched
        if has_matches:
            matched_events.append(event)
    
    print(f"   ✅ Total events with at least one match: {len(matched_events)}")
    
    # Step 4.5: Sort events - arbitrage opportunities first
    print("\n🔀 Sorting events (arbitrage opportunities first)...")
    
    def has_arbitrage(event):
        """Check if event has any arbitrage opportunities."""
        try:
            oddswar_1 = float(event['oddswar']['odds_1'])
            oddswar_x = float(event['oddswar']['odds_x'])
            oddswar_2 = float(event['oddswar']['odds_2'])
            
            # Check all traditional sites for higher odds
            for site in ['roobet', 'stoiximan', 'tumbet']:
                if site in event:
                    site_data = event[site]
                    if (float(site_data['odds_1']) > oddswar_1 or 
                        float(site_data['odds_x']) > oddswar_x or 
                        float(site_data['odds_2']) > oddswar_2):
                        return True
            return False
        except (ValueError, KeyError):
            return False
    
    # Sort: events with arbitrage first (True=1, False=0), reverse to get True first
    matched_events.sort(key=lambda e: has_arbitrage(e), reverse=True)
    
    arb_count = sum(1 for e in matched_events if has_arbitrage(e))
    print(f"   ✅ {arb_count} events with arbitrage at top, {len(matched_events) - arb_count} without at bottom")
    
    # Step 5: Generate HTML
    print("\n📝 Generating HTML output...")
    generate_html(matched_events, 'results.html')
    print(f"   ✅ Written to results.html")
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total Oddswar events: {len(oddswar_events)}")
    print(f"Events with matches: {len(matched_events)}")
    print(f"Events without matches: {len(oddswar_events) - len(matched_events)}")
    print()
    
    # Breakdown by site combinations
    roobet_only = sum(1 for e in matched_events if 'roobet' in e and 'stoiximan' not in e and 'tumbet' not in e)
    stoiximan_only = sum(1 for e in matched_events if 'stoiximan' in e and 'roobet' not in e and 'tumbet' not in e)
    tumbet_only = sum(1 for e in matched_events if 'tumbet' in e and 'roobet' not in e and 'stoiximan' not in e)
    multiple = len(matched_events) - roobet_only - stoiximan_only - tumbet_only
    
    print("Breakdown:")
    print(f"  - Roobet only: {roobet_only}")
    print(f"  - Stoiximan only: {stoiximan_only}")
    print(f"  - Tumbet only: {tumbet_only}")
    print(f"  - Multiple sites: {multiple}")
    print()
    print("✅ Done! Open results.html to view arbitrage opportunities.")
    print("="*80)


if __name__ == '__main__':
    main()

