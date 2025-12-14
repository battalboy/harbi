#!/bin/bash

# Simple script to fetch odds from both Stoiximan and Oddswar

cd "$(dirname "$0")"
source venv/bin/activate

echo "🔵 Fetching Stoiximan data..."
curl -s 'https://en.stoiximan.gr/danae-webapi/api/live/overview/latest?includeVirtuals=false&queryLanguageId=1&queryOperatorId=2' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36' \
  -H 'Accept: application/json' > stoiximan-api.json

if python stoiximan_api_complete_parser.py stoiximan-api.json stoiximan-formatted.txt 2>/dev/null; then
    echo "✓ Stoiximan data fetched successfully"
else
    echo "⚠ Stoiximan fetch failed (geoblocked - check VPN connection to Greece)"
fi

echo ""
echo "🟠 Fetching Oddswar data..."
python oddswar_api_complete_parser.py

echo ""
echo "✅ Done!"
echo ""
echo "📊 Results:"
echo "   Stoiximan: $(grep -c "Team 1" stoiximan-formatted.txt || echo 0) matches"
echo "   Oddswar:   $(grep -c "Team 1" oddswar-formatted.txt || echo 0) matches"
echo ""
echo "Output files:"
echo "   stoiximan-formatted.txt"
echo "   oddswar-formatted.txt"

