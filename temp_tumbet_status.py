#!/usr/bin/env python3
"""
Simple Tumbet API status check - returns HTTP response codes only.
"""
import requests

BASE_URL = "https://analytics-sp.googleserv.tech"
LANGUAGE = "ot"

endpoints = [
    f"{BASE_URL}/api/sport/getheader/{LANGUAGE}",
    f"{BASE_URL}/api/live/getlivegames/{LANGUAGE}",
]

if __name__ == "__main__":
    print("Tumbet API status check\n" + "=" * 50)
    for url in endpoints:
        try:
            r = requests.get(url, timeout=10)
            print(f"{r.status_code}  {url}")
        except Exception as e:
            print(f"ERR     {url}  ({e})")
