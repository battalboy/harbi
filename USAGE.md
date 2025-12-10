# Harbi Odds Fetcher - Quick Start

## Run Both Parsers

Simply run:

```bash
./fetch_odds.sh
```

That's it! 🚀

## Output

The script creates two files:
- **`stoiximan-formatted.txt`** - Live soccer matches from Stoiximan (esports filtered out)
- **`oddswar-formatted.txt`** - Live soccer matches from Oddswar

Each line contains:
```
Team 1: [name] | Team 2: [name] | Team 1 Win: [odds] | Draw: [odds] | Team 2 Win: [odds] | Link: [url]
```

## Manual Usage (if needed)

**Stoiximan only:**
```bash
curl -s 'https://en.stoiximan.gr/danae-webapi/api/live/overview/latest?includeVirtuals=false&queryLanguageId=1&queryOperatorId=2' \
  -H 'User-Agent: Mozilla/5.0' -H 'Accept: application/json' > stoiximan-api.json
python stoiximan_api_complete_parser.py stoiximan-api.json stoiximan-formatted.txt
```

**Oddswar only:**
```bash
python oddswar_api_complete_parser.py
```

## Notes

- **Stoiximan** is geoblocked outside Greece - requires VPN connected to Greek IP
  - If fetch fails, check your VPN connection to Greece
- **Oddswar** fetches directly from API (no geoblocking, more reliable)
- Both output files are overwritten each time (always fresh data)

