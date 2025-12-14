#!/usr/bin/env python3
"""
Try different variations of known working endpoints
"""
import requests
import json

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/json'
}

BASE = 'https://en.stoiximan.gr/danae-webapi/api'

# We know /live/overview/latest works, let's try variations
endpoints = [
    # Try without filters
    '/live/overview/latest',
    
    # Try different time scopes
    '/live/overview/all?queryLanguageId=1&queryOperatorId=2',
    '/live/all?queryLanguageId=1&queryOperatorId=2',
    
    # Try getting sport structure
    '/live/overview?queryLanguageId=1&queryOperatorId=2',
    '/overview/latest?queryLanguageId=1&queryOperatorId=2',
    
    # Try prematch (upcoming matches)
    '/prematch?queryLanguageId=1&queryOperatorId=2',
    '/betting/prematch?queryLanguageId=1&queryOperatorId=2',
    
    # Try search/browse
    '/browse?queryLanguageId=1&queryOperatorId=2',
    '/sportsbook?queryLanguageId=1&queryOperatorId=2',
    
    # Try getting competitions list
    '/live/competitions?sportId=1&queryLanguageId=1&queryOperatorId=2',
    '/competitions/list?sportId=1&queryLanguageId=1&queryOperatorId=2',
]

print("🔍 EXPLORING STOIXIMAN API - ROUND 2")
print("="*60)
print()

successful = []

for endpoint in endpoints:
    url = BASE + endpoint
    print(f"Testing: {endpoint[:60]}")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        
        if response.status_code == 200:
            try:
                data = response.json()
                size = len(response.text)
                print(f"  ✅ SUCCESS! Size: {size:,} bytes")
                
                # Analyze structure
                if isinstance(data, dict):
                    keys = list(data.keys())
                    print(f"     Type: dict with keys: {keys[:8]}")
                    
                    # Look for event counts
                    for key in ['events', 'sports', 'competitions', 'markets']:
                        if key in data:
                            count = len(data[key]) if isinstance(data[key], list) else 'N/A'
                            print(f"     {key}: {count}")
                    
                    successful.append((endpoint, size, keys))
                elif isinstance(data, list):
                    print(f"     Type: list with {len(data)} items")
                    successful.append((endpoint, size, 'list'))
                    
            except:
                print(f"  ✅ SUCCESS (200) but not JSON - Size: {len(response.text):,} bytes")
        else:
            print(f"  ❌ Status {response.status_code}")
    
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:60]}")
    
    print()

if successful:
    print("="*60)
    print(f"\n🎉 FOUND {len(successful)} WORKING ENDPOINT(S)!\n")
    for endpoint, size, info in successful:
        print(f"✅ {endpoint}")
        print(f"   Size: {size:,} bytes, Info: {info}\n")

