#!/usr/bin/env python3
"""
Explore Stoiximan API endpoints to find team lists
"""
import requests
import json

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/json'
}

BASE_URL = 'https://en.stoiximan.gr/danae-webapi/api'

# Potential endpoints to try
endpoints = [
    # Team/Sports info
    '/sports',
    '/sports/1',  # Soccer
    '/teams',
    '/markets',
    
    # Different match types
    '/prematch/overview/latest?queryLanguageId=1&queryOperatorId=2',
    '/upcoming/overview/latest?queryLanguageId=1&queryOperatorId=2',
    '/today/overview/latest?queryLanguageId=1&queryOperatorId=2',
    '/all/overview/latest?queryLanguageId=1&queryOperatorId=2',
    
    # Soccer specific
    '/prematch/sport/1?queryLanguageId=1&queryOperatorId=2',
    '/live/sport/1?queryLanguageId=1&queryOperatorId=2',
    
    # Other attempts
    '/events?sportId=1',
    '/competitions?sportId=1',
    '/search/teams',
]

print("🔍 EXPLORING STOIXIMAN API ENDPOINTS")
print("="*60)
print()

for endpoint in endpoints:
    url = BASE_URL + endpoint
    print(f"Testing: {endpoint}")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ SUCCESS (200) - Response size: {len(response.text)} bytes")
            
            # Try to identify what we got
            if isinstance(data, dict):
                print(f"     Keys: {list(data.keys())[:5]}")
                if 'sports' in data:
                    print(f"     Found {len(data['sports'])} sports")
                if 'events' in data:
                    print(f"     Found {len(data['events'])} events")
                if 'competitions' in data:
                    print(f"     Found {len(data['competitions'])} competitions")
            elif isinstance(data, list):
                print(f"     List with {len(data)} items")
        else:
            print(f"  ❌ Status {response.status_code}")
    
    except requests.exceptions.Timeout:
        print(f"  ⏱️  Timeout")
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Error: {str(e)[:50]}")
    except Exception as e:
        print(f"  ❌ Parse error: {str(e)[:50]}")
    
    print()

print("="*60)
print("✅ Exploration complete")
