#!/usr/bin/env python3
"""
Simple Tumbet API status check - returns HTTP response codes and latency.
"""
import requests
import time

BASE_URL = "https://analytics-sp.googleserv.tech"
LANGUAGE = "ot"
REQUEST_TIMEOUT = 120

endpoints = [
    f"{BASE_URL}/api/sport/getheader/{LANGUAGE}",
    f"{BASE_URL}/api/live/getlivegames/{LANGUAGE}",
]

if __name__ == "__main__":
    print("Tumbet API status check\n" + "=" * 50)
    for url in endpoints:
        try:
            start = time.time()
            r = requests.get(url, timeout=REQUEST_TIMEOUT)
            elapsed = time.time() - start
            print(f"{r.status_code}  {elapsed:.1f}s  {url}")
        except Exception as e:
            print(f"ERR     {url}  ({e})")
