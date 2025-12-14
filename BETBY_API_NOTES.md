# Betby API Investigation Notes

## Overview

Betby is a sports betting platform provider that powers multiple sportsbook sites including Roobet. Their API structure is consistent across all brands.

**Demo Site:** https://demo.betby.com/sportsbook/sidebar/?top=%2Fsoccer-1

## API Structure

### Base URLs
- **Roobet:** `https://api-g-c7818b61-607.sptpub.com`
- **Betby Demo:** `https://demoapi.betby.com`
- Pattern: Each brand has its own subdomain but identical endpoint structure

### Brand IDs
- **Roobet:** `2186449803775455232`
- **Betby Demo:** `1653815133341880320`

## Endpoints

### Two-Step Version System

Betby uses a two-step process to fetch data:

#### Step 1: Get Current Version
```
GET /api/v4/{type}/brand/{brand_id}/en/0
```
- `{type}`: `live` or `prematch`
- Returns: 
```json
{
  "version": 1765737128923,
  "top_events_versions": [1765737128923],
  "rest_events_versions": [1765737128924, 1765737128925, 1765737128926],
  ...
}
```

#### Step 2: Fetch Events Data (MULTIPLE VERSIONS!)
**🎯 KEY DISCOVERY:** For prematch, you must fetch from ALL version endpoints!

```
GET /api/v4/{type}/brand/{brand_id}/en/{version}
```

**For PREMATCH only:**
- Fetch from `version` → ~15 soccer matches (~30 teams)
- Fetch from each `top_events_versions` → same as main version
- **Fetch from each `rest_events_versions` → 160+ soccer matches each!**

**Total: ~497 soccer matches, 700+ unique teams in one collection cycle!**

This is the secret to getting comprehensive team data without waiting days/weeks.

### Example Code:
```python
# Step 1: Get manifest
manifest_url = f"{BASE_URL}/api/v4/prematch/brand/{BRAND_ID}/en/0"
manifest = requests.get(manifest_url).json()

# Step 2: Collect ALL versions
versions = [manifest['version']]
versions.extend(manifest.get('top_events_versions', []))
versions.extend(manifest.get('rest_events_versions', []))  # ← KEY!

# Step 3: Fetch from each version and combine
all_teams = set()
for version in versions:
    events_url = f"{BASE_URL}/api/v4/prematch/brand/{BRAND_ID}/en/{version}"
    data = requests.get(events_url).json()
    # Extract teams from data['events']...
```

### Available Types
1. **`live`** - Currently live matches
2. **`prematch`** - Upcoming matches (not yet started)

### Headers Required
```
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36
Accept: application/json
Origin: https://{site}.com
Referer: https://{site}.com/sports/soccer-1
```

## Data Structure

### Response Format
```json
{
  "epoch": 1765737128923,
  "version": 1765737128923,
  "generated": 1765737128923,
  "snapshot_complete": true,
  "fixtures_complete": true,
  "status": {...},
  "sports": {...},
  "categories": {...},
  "tournaments": {...},
  "events": {
    "2611556000905433113": {
      "desc": {
        "scheduled": 1765731600,
        "type": "match",
        "slug": "team-a-team-b",
        "sport": "1",  // "1" = Soccer
        "category": "...",
        "tournament": "...",
        "competitors": [
          {
            "id": "2492342503257288753",
            "sport_id": "1",
            "name": "Team A"
          },
          {
            "id": "431229",
            "sport_id": "1",
            "name": "Team B"
          }
        ]
      },
      "markets": {...},
      "state": {...},
      "score": {...}
    }
  }
}
```

### Extracting Team Names
Team names are located at:
```
events[event_id]['desc']['competitors'][index]['name']
```

### Sport IDs
- `"1"` = Soccer/Football
- `"23"` = Volleyball
- `"2"` = Basketball
- Other IDs for other sports

## Key Findings

### ✅ Advantages over Stoiximan
1. **Both Live AND Prematch**: Stoiximan only provides live matches
2. **MULTIPLE VERSION ENDPOINTS**: The `rest_events_versions` unlock 700+ teams!
3. **Much faster collection**: Get 727 teams in ONE run (vs waiting days/weeks)
4. **More complete data**: Can collect all upcoming matches at once
5. **Consistent structure**: Same API across all Betby-powered sites
6. **No geography restrictions**: Works without VPN (unlike Stoiximan)

### ✅ Advantages over Oddswar
1. **Similar coverage**: Roobet ~727 teams vs Oddswar ~1323 teams
2. **No pagination needed**: Get all data in single collection cycle
3. **Both live and prematch**: More comprehensive than live-only

### 🎯 THE CRITICAL DISCOVERY

**The `rest_events_versions` array is the key!**

When you call:
```
GET /api/v4/prematch/brand/{BRAND_ID}/en/0
```

You get back:
```json
{
  "version": 1765737363585,
  "rest_events_versions": [1765737363586, 1765737363587, 1765737363588]
}
```

Each of these rest_events_versions contains ~160 additional soccer matches!

- Main version: 15 soccer matches
- rest_events_versions[0]: 162 soccer matches ← 🎯
- rest_events_versions[1]: 162 soccer matches ← 🎯  
- rest_events_versions[2]: 143 soccer matches ← 🎯

**Total: 497 soccer matches, 727 unique teams!**

### ✅ API Accessibility
- ✅ No authentication required
- ✅ Standard HTTP requests work
- ✅ CORS headers accepted
- ✅ Publicly accessible

### ⚠️ Considerations
- Version numbers change frequently (every few seconds)
- Must use two-step process (can't guess version)
- Data is real-time, updates constantly

## Implementation

### Current Collector Script
`collect_roobet_teams.py` implements this API pattern:
- Fetches both live AND prematch matches
- Filters for soccer only (sport_id = '1')
- Runs every 60-120 seconds
- Outputs to `roobet_names.txt`

### Adaptable to Other Sites
The same script structure can be used for any Betby-powered sportsbook:
1. Identify the brand ID (from browser network tab)
2. Identify the base URL (usually `api-*.sptpub.com` or `*api.betby.com`)
3. Update script configuration
4. Run collector

## Testing Summary

### Roobet (Production)
- ✅ Working perfectly
- 📈 ~200 live events, ~400 prematch events
- ⚽ **727 unique soccer teams** (using rest_events_versions!)
- 🚀 Can collect all teams in ONE run (~10 seconds)

### Betby Demo
- ✅ Working perfectly
- 📈 Similar event counts
- ⚽ Same multi-version structure
- ✅ Publicly accessible for testing

### Comparison with Other Sportsbooks

| Sportsbook | Teams Collected | Collection Method | Time Required |
|------------|----------------|-------------------|---------------|
| **Roobet** | **727** | Single API call (multi-version) | **~10 seconds** |
| Oddswar | 1,323 | Paginated API (interval=all) | ~30 seconds |
| Stoiximan | 3,228 | Live-only (over time) | Days/weeks |

Both APIs use **identical structure** - confirms our implementation is correct.

## URLs Reference

- **Betby Demo Site:** https://demo.betby.com/sportsbook/sidebar/?top=%2Fsoccer-1
- **Roobet Soccer Page:** https://roobet.com/sports/soccer-1
- **Demo API Example:** https://demoapi.betby.com/api/v4/live/brand/1653815133341880320/en/0

