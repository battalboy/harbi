#!/usr/bin/env python3
"""
Simple Roobet API status check - returns HTTP response codes only.
Uses same endpoints and headers as event_create_roobet.py.
"""
import requests
import time

BASE_URL = "https://api-g-c7818b61-607.sptpub.com"
BRAND_ID = "2186449803775455232"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json",
    "Origin": "https://roobet.com",
    "Referer": "https://roobet.com/sports/soccer-1",
}

endpoints = [
    f"{BASE_URL}/api/v4/prematch/brand/{BRAND_ID}/en/0",
    f"{BASE_URL}/api/v4/live/brand/{BRAND_ID}/en/0",
]

if __name__ == "__main__":
    print("Roobet API status check\n" + "=" * 50)
    for url in endpoints:
        try:
            start = time.time()
            r = requests.get(url, headers=HEADERS, timeout=10)
            elapsed = time.time() - start
            print(f"{r.status_code}  {elapsed:.1f}s  {url}")
        except Exception as e:
            print(f"ERR     {url}  ({e})")
