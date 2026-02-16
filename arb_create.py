#!/usr/bin/env python3
"""
Arbitrage Opportunity Detector

Matches events across Oddswar (exchange) and traditional bookmakers
(Roobet, Stoiximan, Tumbet) to identify potential arbitrage opportunities.

Uses team name mappings from CSV files and event data from formatted text files.
"""

import csv
import json
import os
import requests
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from zoneinfo import ZoneInfo


def load_error_status(site_name: str) -> Optional[Dict]:
    """
    Load error status from error log file.
    
    Args:
        site_name: Name of site (lowercase, e.g., 'oddswar', 'roobet')
    
    Returns:
        Error dict if error occurred, None if success or file doesn't exist
    """
    error_file = f"{site_name}-error.json"
    
    try:
        with open(error_file, 'r', encoding='utf-8') as f:
            error_data = json.load(f)
            
            # Return error data if there was an error
            if error_data.get('error', False):
                return error_data
            else:
                return None
    except FileNotFoundError:
        # No error file = assume success (backward compatibility)
        return None
    except Exception as e:
        # If we can't read error file, return generic error
        return {
            'site': site_name.capitalize(),
            'error': True,
            'error_type': 'FileReadError',
            'error_message': f"❌ HATA: Error dosyası okunamadı - {str(e)}"
        }


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
    Returns dict: {(team1, team2): {odds_1, odds_x, odds_2, link, status, league, start_time}}
    
    Status, league, and start_time are optional (only present in Oddswar files).
    """
    events = {}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            # Parse: Team 1: X | Team 2: Y | Team 1 Win: Z | Draw: Z | Team 2 Win: Z | Link: URL [| Status: ...] [| League: ...] [| Start Time: ISO8601]
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
                
                # Optional status, league, start_time (only in Oddswar files)
                status = None
                if len(parts) >= 7:
                    status = parts[6].split(':', 1)[1].strip()
                league = None
                if len(parts) >= 8:
                    league = parts[7].split(':', 1)[1].strip()
                start_time = None
                if len(parts) >= 9:
                    start_time = parts[8].split(':', 1)[1].strip()
                
                # Skip if any odds are N/A
                if odds_1 == 'N/A' or odds_x == 'N/A' or odds_2 == 'N/A':
                    continue
                
                event_data = {
                    'odds_1': odds_1,
                    'odds_x': odds_x,
                    'odds_2': odds_2,
                    'link': link
                }
                if status:
                    event_data['status'] = status
                if league:
                    event_data['league'] = league
                if start_time:
                    event_data['start_time'] = start_time
                
                events[(team1, team2)] = event_data
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


def format_turkish_datetime(iso_timestamp: str) -> str:
    """
    Format ISO 8601 timestamp to Turkish date/time format.
    Example: "2026-01-29T23:30:00.000Z" -> "Tarih: <b>29 Ocak 2026</b> - Saat: <b>23:30</b>"
    """
    turkish_months = {
        1: 'Ocak', 2: 'Şubat', 3: 'Mart', 4: 'Nisan', 5: 'Mayıs', 6: 'Haziran',
        7: 'Temmuz', 8: 'Ağustos', 9: 'Eylül', 10: 'Ekim', 11: 'Kasım', 12: 'Aralık'
    }
    try:
        dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
        date_str = f"{dt.day} {turkish_months[dt.month]} {dt.year}"
        time_str = dt.strftime('%H:%M')
        return f"Tarih: <b>{date_str}</b> - Saat: <b>{time_str}</b>"
    except Exception:
        return f"Tarih: <b>N/A</b> - Saat: <b>N/A</b>"


def generate_error_banner(error_statuses: Dict[str, Optional[Dict]]) -> str:
    """
    Generate HTML for error banner showing site connection errors.
    Returns empty string if no errors.
    
    Args:
        error_statuses: Dict of error statuses {'oddswar': error_dict, 'roobet': error_dict, ...}
    
    Returns:
        HTML string for error banner or empty string
    """
    # Check if there are any errors
    errors = {site: error for site, error in error_statuses.items() if error is not None}
    
    if not errors:
        return ""
    
    # Special heading if Oddswar failed (master key site)
    if 'oddswar' in errors:
        heading = "⚠️ UYARI - Oddswar Site Bağlantı Hatalası var. Oddswar ana arbing sitesi olduğu için hiç bir oran gözükmeyecek."
    else:
        heading = "⚠️ UYARI - Site Bağlantı Hataları var. Aşağıdaki sitelerin oranları gözükmeyecek."
    
    # Build error banner HTML
    banner = f"""
    <div style="width: 80%; margin: 20px auto; padding: 20px; background-color: #fff3cd; border: 2px solid #ffc107; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); box-sizing: border-box;">
        <h2 style="margin-top: 0; color: #856404;">{heading}</h2>
"""
    
    for site_name, error_data in errors.items():
        site_display = site_name.capitalize()
        error_msg = error_data.get('error_message', '❌ HATA: Bilinmeyen hata')
        
        banner += f"""        <div style="margin: 10px 0; padding: 10px; background-color: #ffe8a1; border-left: 4px solid #ff6b6b; border-radius: 3px;">
            <strong style="color: #721c24;">{site_display}:</strong> <span style="color: #856404;">{error_msg}</span>
        </div>
"""
    
    banner += """    </div>
"""
    
    return banner


def generate_html(matched_events: List[Dict], output_file: str = 'results.html', 
                  error_statuses: Dict[str, Optional[Dict]] = None):
    """
    Generate HTML file with matched events in table format.
    
    Args:
        matched_events: List of dicts containing event data and matches
        output_file: Path to output HTML file
        error_statuses: Dict of error statuses {'oddswar': error_dict, 'roobet': error_dict, ...}
    """
    if error_statuses is None:
        error_statuses = {}
    
    # Generate timestamp in GMT
    timestamp = datetime.utcnow().strftime('%b %d %Y - %H:%M:%S')
    
    # HTML header
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Harbi - Soccer Arbitrage Results</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        
        .event-table {{
            width: 80%;
            margin: 20px auto;
            border-collapse: collapse;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .event-table th {{
            background-color: #e0e0e0;
            padding: 10px;
            text-align: center;
            border: 1px solid #ccc;
        }}
        
        .event-table td {{
            padding: 10px;
            text-align: center;
            border: 1px solid #ccc;
        }}
        
        .site-name {{
            font-weight: bold;
            text-align: left;
        }}
        
        .header-row {{
            background-color: #d0d0d0;
            font-size: 1.1em;
        }}
        
        .arb-opportunity {{
            background-color: #dc3545;
            color: white;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <h1 style="text-align: center;">H.Ar.B.İ. - Futbol Arbitrage Oran Sonuçları - {timestamp}</h1>
"""
    
    # Add error banner if there are any errors
    html += generate_error_banner(error_statuses)
    
    # Add event tables
    for event in matched_events:
        team1 = event['team1']
        team2 = event['team2']
        oddswar = event['oddswar']
        
        # Get status, league, start time from Oddswar data (aligned with arb_basketball_create)
        status = oddswar.get('status', 'Gelen Maç')
        league = oddswar.get('league', 'N/A')
        start_time = oddswar.get('start_time')
        datetime_str = format_turkish_datetime(start_time) if start_time and start_time != 'N/A' else None
        
        if datetime_str:
            header_content = f"{team1} VS {team2} ({status})<br><span style=\"font-weight: normal; font-size: 0.9em;\">Lig: {league}<br>{datetime_str}</span>"
        else:
            header_content = f"{team1} VS {team2} ({status})<br><span style=\"font-weight: normal; font-size: 0.9em;\">Lig: {league}</span>"
        
        # Start table
        html += f"""
    <!-- Event: {team1} vs {team2} -->
    <table class="event-table">
        <thead>
            <tr class="header-row">
                <th colspan="4">{header_content}</th>
            </tr>
        </thead>
        <tbody>
"""
        
        # Oddswar row (always shown - it's the master)
        html += f"""            <tr>
                <td class="site-name"><a href="{oddswar['link']}" target="_blank">Oddswar oranları</a></td>
                <td>{oddswar['odds_1']}</td>
                <td>{oddswar['odds_x']}</td>
                <td>{oddswar['odds_2']}</td>
            </tr>
"""
        
        # Add Tumbet row if matched
        if 'tumbet' in event:
            tumbet = event['tumbet']
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


def load_telegram_config():
    """
    Load Telegram configuration from harbi-config.py.
    
    Returns:
        list: List of telegram users from config, or empty list if not configured
    """
    try:
        config = {}
        with open('harbi-config.py', 'r', encoding='utf-8') as f:
            exec(f.read(), config)
        
        return config.get('TELEGRAM_USERS', [])
    except FileNotFoundError:
        print("   ⚠️  harbi-config.py not found")
        return []
    except Exception as e:
        print(f"   ⚠️  Error loading config: {e}")
        return []


def send_telegram_message(chat_id: int, message: str, bot_token: str) -> bool:
    """
    Send a Telegram message with HTML formatting.
    
    Args:
        chat_id: Telegram user chat ID
        message: Message text (HTML formatted)
        bot_token: Telegram bot token
    
    Returns:
        bool: True if successful
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    try:
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            return True
        else:
            print(f"      ⚠️  Failed to send to {chat_id} (status: {response.status_code})")
            return False
    except Exception as e:
        print(f"      ⚠️  Error sending to {chat_id}: {str(e)[:50]}")
        return False


def build_telegram_block(event: Dict, site_name: str) -> str:
    """
    Build a single Telegram message block for one arbitrage opportunity.
    Reuses odds comparison logic from generate_html().
    
    Args:
        event: Event dict with oddswar and traditional site data
        site_name: Name of traditional site ('roobet', 'stoiximan', 'tumbet')
    
    Returns:
        str: Formatted message block with <pre> and links
    """
    team1 = event['team1']
    team2 = event['team2']
    oddswar = event['oddswar']
    site_data = event[site_name]
    
    # Site display names
    site_display = {
        'roobet': 'Roobet',
        'stoiximan': 'Stoiximan',
        'tumbet': 'Tumbet'
    }
    
    # Build odds strings with highlighting (reuse logic from HTML generation)
    try:
        # Oddswar odds
        oddswar_1 = float(oddswar['odds_1'])
        oddswar_x = float(oddswar['odds_x'])
        oddswar_2 = float(oddswar['odds_2'])
        
        # Traditional site odds
        site_1 = float(site_data['odds_1'])
        site_x = float(site_data['odds_x'])
        site_2 = float(site_data['odds_2'])
        
        # Highlight BOTH sides where traditional > oddswar
        # Oddswar line
        oddswar_1_str = f"<b><u>{oddswar['odds_1']}</u></b>" if site_1 > oddswar_1 else oddswar['odds_1']
        oddswar_x_str = f"<b><u>{oddswar['odds_x']}</u></b>" if site_x > oddswar_x else oddswar['odds_x']
        oddswar_2_str = f"<b><u>{oddswar['odds_2']}</u></b>" if site_2 > oddswar_2 else oddswar['odds_2']
        
        # Traditional site line
        site_1_str = f"<b><u>{site_data['odds_1']}</u></b>" if site_1 > oddswar_1 else site_data['odds_1']
        site_x_str = f"<b><u>{site_data['odds_x']}</u></b>" if site_x > oddswar_x else site_data['odds_x']
        site_2_str = f"<b><u>{site_data['odds_2']}</u></b>" if site_2 > oddswar_2 else site_data['odds_2']
        
    except (ValueError, KeyError):
        # Fallback if conversion fails
        oddswar_1_str = oddswar['odds_1']
        oddswar_x_str = oddswar['odds_x']
        oddswar_2_str = oddswar['odds_2']
        site_1_str = site_data['odds_1']
        site_x_str = site_data['odds_x']
        site_2_str = site_data['odds_2']
    
    # Build the block (without <pre> so HTML formatting works)
    block = f"""Maç: {team1} vs {team2}
Oddswar: {oddswar_1_str} | {oddswar_x_str} | {oddswar_2_str}
{site_display[site_name]}:  {site_1_str} | {site_x_str} | {site_2_str}

<a href="{oddswar['link']}">Oddswar Linki</a>
<a href="{site_data['link']}">{site_display[site_name]} Linki</a>

"""
    
    return block


def send_telegram_notifications(matched_events: List[Dict], arb_count: int):
    """
    Send Telegram notifications about arbitrage opportunities to all configured users.
    Uses smart message splitting to handle Telegram's 4096 character limit.
    
    Args:
        matched_events: List of matched events (already sorted with arbitrage first)
        arb_count: Number of events with arbitrage opportunities
    """
    # Only send if there are arbitrage opportunities
    if arb_count == 0:
        return
    
    print("\n📱 Sending Telegram notifications...")
    
    # Load config
    telegram_users = load_telegram_config()
    
    if not telegram_users:
        print("   ⚠️  No Telegram users configured (skipping)")
        return
    
    # Get bot token from environment
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '8272624197:AAEHXPYrE0E9-hjazYJrcogUTYSH-FM5_SA')
    
    # Build message blocks for events with arbitrage
    print(f"   Building messages for {arb_count} arbitrage opportunities...")
    
    # Get current time in Athens timezone
    now = datetime.now(ZoneInfo('Europe/Athens'))
    turkish_months = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 
                      'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
    timestamp = f"{now.day} {turkish_months[now.month-1]} {now.year} - {now.hour:02d}:{now.minute:02d}"
    
    # Web URL for soccer results page (adjust domain/port as needed)
    web_url = "http://89.125.255.32:8080/results.html"
    
    header = f"""⚽ *Yeni Futbol Harbi Oran Fırsatları Var*
📅 {timestamp}
Bu sayfanın web versiyonunu görmek için <a href="{web_url}">tıklayın</a>...

"""
    blocks = []
    
    for event in matched_events:
        # Only include events with arbitrage (reuse has_arbitrage logic inline)
        has_arb = False
        try:
            oddswar_1 = float(event['oddswar']['odds_1'])
            oddswar_x = float(event['oddswar']['odds_x'])
            oddswar_2 = float(event['oddswar']['odds_2'])
            
            for site in ['roobet', 'stoiximan', 'tumbet']:
                if site in event:
                    site_data = event[site]
                    if (float(site_data['odds_1']) > oddswar_1 or 
                        float(site_data['odds_x']) > oddswar_x or 
                        float(site_data['odds_2']) > oddswar_2):
                        has_arb = True
                        # Build block for this site
                        block = build_telegram_block(event, site)
                        blocks.append(block)
                        break  # Only one block per event (first matching site)
        except (ValueError, KeyError):
            continue
        
        if not has_arb:
            break  # Events are sorted, so we can stop when we hit non-arbitrage events
    
    if not blocks:
        print("   ⚠️  No arbitrage blocks built (this shouldn't happen)")
        return
    
    # Smart message splitting (never split a block)
    print(f"   Splitting into messages (max 4096 chars per message)...")
    
    messages = []
    current_message = header
    
    for block in blocks:
        # Check if adding this block would exceed limit
        if len(current_message) + len(block) > 4096:
            # Send current message and start a new one
            messages.append(current_message)
            current_message = header + block
        else:
            current_message += block
    
    # Add final message
    if current_message != header:
        messages.append(current_message)
    
    print(f"   Created {len(messages)} message(s)")
    
    # Send to all users
    total_sent = 0
    for user in telegram_users:
        user_name = user.get('name', 'Unknown')
        user_id = user.get('id')
        
        if not user_id:
            continue
        
        print(f"   Sending to {user_name} ({user_id})...")
        
        user_success = 0
        for i, message in enumerate(messages, 1):
            if send_telegram_message(user_id, message, bot_token):
                user_success += 1
        
        if user_success == len(messages):
            print(f"      ✅ All {len(messages)} message(s) sent successfully")
            total_sent += 1
        else:
            print(f"      ⚠️  Only {user_success}/{len(messages)} message(s) sent")
    
    print(f"   📊 Notifications sent to {total_sent}/{len(telegram_users)} users")


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
    
    # Step 2: Load events and check for errors
    print("\n📂 Loading events from formatted files...")
    
    # Load error statuses
    oddswar_error = load_error_status('oddswar')
    roobet_error = load_error_status('roobet')
    stoiximan_error = load_error_status('stoiximan')
    tumbet_error = load_error_status('tumbet')
    
    # Load events (will be empty if there was an error)
    oddswar_events = parse_formatted_file('oddswar-formatted.txt')
    roobet_events = parse_formatted_file('roobet-formatted.txt')
    stoiximan_events = parse_formatted_file('stoiximan-formatted.txt')
    tumbet_events = parse_formatted_file('tumbet-formatted.txt')
    
    # Print status
    if oddswar_error:
        print(f"   ❌ Oddswar: ERROR - {oddswar_error['error_type']}")
    else:
        print(f"   ✅ Oddswar: {len(oddswar_events)} events")
    
    if roobet_error:
        print(f"   ❌ Roobet: ERROR - {roobet_error['error_type']}")
    else:
        print(f"   ✅ Roobet: {len(roobet_events)} events")
    
    if stoiximan_error:
        print(f"   ❌ Stoiximan: ERROR - {stoiximan_error['error_type']}")
    else:
        print(f"   ✅ Stoiximan: {len(stoiximan_events)} events")
    
    if tumbet_error:
        print(f"   ❌ Tumbet: ERROR - {tumbet_error['error_type']}")
    else:
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
    
    # Pass error statuses to HTML generator
    error_statuses = {
        'oddswar': oddswar_error,
        'roobet': roobet_error,
        'stoiximan': stoiximan_error,
        'tumbet': tumbet_error
    }
    
    generate_html(matched_events, 'results.html', error_statuses)
    print(f"   ✅ Written to results.html")
    
    # Step 6: Send Telegram notifications if arbitrage found
    send_telegram_notifications(matched_events, arb_count)
    
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

