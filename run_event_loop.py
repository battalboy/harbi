#!/usr/bin/env python3
"""
Harbi Event Fetching Daemon

Continuously fetches live odds from betting sites with randomized intervals.
Reads harbi-config.py for runtime configuration (no restart needed).
"""

import time
import random
import requests
import os
from datetime import datetime


# Telegram configuration
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '8272624197:AAEHXPYrE0E9-hjazYJrcogUTYSH-FM5_SA')
JAMES_CHAT_ID = 1580648939


def send_telegram_message(chat_id: int, message: str):
    """Send a Telegram message to a specific chat ID."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    try:
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Message sent to {chat_id}")
            return True
        else:
            print(f"❌ Failed to send message (status: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return False


def get_random_interval():
    """Get random interval between 3 and 5 minutes (in seconds)."""
    # Random between 180 and 300 seconds (3 to 5 minutes)
    return random.randint(180, 300)


def main():
    """Main daemon loop."""
    print("="*80)
    print("HARBI EVENT LOOP DAEMON - STARTED")
    print("="*80)
    print(f"Bot Token: {TELEGRAM_BOT_TOKEN[:20]}...")
    print(f"Target: James (Chat ID: {JAMES_CHAT_ID})")
    print("\nPress Ctrl+C to stop\n")
    
    cycle_count = 0
    
    try:
        while True:
            cycle_count += 1
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            print(f"\n{'='*80}")
            print(f"CYCLE #{cycle_count} - {timestamp}")
            print(f"{'='*80}")
            
            # Send trigger message
            print("📱 Sending trigger message to James...")
            send_telegram_message(JAMES_CHAT_ID, "Trigger!")
            
            # Get random interval
            interval_seconds = get_random_interval()
            interval_minutes = interval_seconds / 60
            
            print(f"\n⏱️  Next trigger in {interval_minutes:.1f} minutes ({interval_seconds} seconds)")
            print(f"   Waiting until: {datetime.fromtimestamp(time.time() + interval_seconds).strftime('%H:%M:%S')}")
            
            # Wait for random interval
            time.sleep(interval_seconds)
    
    except KeyboardInterrupt:
        print("\n\n" + "="*80)
        print("DAEMON STOPPED BY USER")
        print("="*80)
        print(f"Total cycles completed: {cycle_count}")
        print("\nGoodbye!")


if __name__ == '__main__':
    main()
