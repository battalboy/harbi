#!/usr/bin/env python3
"""
Telegram Notification Module for Harbi
Copy these functions into arb_create.py when ready
"""

import requests
import os

# TELEGRAM CONFIGURATION
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '8272624197:AAEHXPYrE0E9-hjazYJrcogUTYSH-FM5_SA')
TELEGRAM_CHAT_IDS = os.environ.get('TELEGRAM_CHAT_IDS', '').split(',')
TELEGRAM_CHAT_IDS = [int(cid.strip()) for cid in TELEGRAM_CHAT_IDS if cid.strip()]


def send_telegram_notification(matched_events):
    """Send Telegram notification about arbitrage opportunities"""
    
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_IDS:
        print("   ⚠️  Telegram not configured (skipping notifications)")
        return
    
    # Create message
    message = f"🚨 *HARBI - Arbitrage Alert*\n\n"
    message += f"Found *{len(matched_events)}* arbitrage opportunities!\n\n"
    
    # Add top 5 events
    for i, event in enumerate(matched_events[:5], 1):
        team1 = event['team1']
        team2 = event['team2']
        message += f"{i}. {team1} vs {team2}\n"
        
        # Show which sites have opportunities
        sites = []
        if 'roobet' in event:
            sites.append('Roobet')
        if 'stoiximan' in event:
            sites.append('Stoiximan')
        if 'tumbet' in event:
            sites.append('Tumbet')
        message += f"   Sites: {', '.join(sites)}\n\n"
    
    if len(matched_events) > 5:
        message += f"... and {len(matched_events) - 5} more\n\n"
    
    message += f"🌐 Check results.html for details"
    
    # Send to all clients
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    for chat_id in TELEGRAM_CHAT_IDS:
        try:
            payload = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                print(f"   ✅ Notification sent to chat {chat_id}")
            else:
                print(f"   ❌ Failed to send to chat {chat_id}")
        except Exception as e:
            print(f"   ❌ Error: {e}")


# EXAMPLE: How to call it in arb_create.py main() function
# Add this after line 408 where it says:
# print(f"   ✅ Total events with arbitrage opportunities: {len(matched_events)}")
#
# if len(matched_events) > 0:
#     print("\n📱 Sending Telegram notifications...")
#     send_telegram_notification(matched_events)
