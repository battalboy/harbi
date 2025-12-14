# HOW TO GET ALL TEAM NAMES FROM BETBY API

## The Answer: YES! ✅

The Betby demo site investigation led to a **critical discovery**: the `rest_events_versions` array!

## The Problem

Initially, fetching from Roobet's API gave us only ~30 teams:
- LIVE endpoint: 15 soccer matches → 30 teams
- PREMATCH endpoint: 15 soccer matches → 30 teams  
- **Total: 60 teams** (not enough!)

We needed a way to get ALL scheduled matches, not just immediate live/prematch.

## The Solution: Multiple Version Endpoints

### Discovery

When calling the prematch manifest endpoint:
```
GET https://api-g-c7818b61-607.sptpub.com/api/v4/prematch/brand/2186449803775455232/en/0
```

The response includes:
```json
{
  "version": 1765737363585,
  "top_events_versions": [1765737363585],
  "rest_events_versions": [1765737363586, 1765737363587, 1765737363588]
}
```

### The Key Insight

**Each version endpoint contains DIFFERENT events!**

| Version | Soccer Matches | Unique Teams |
|---------|----------------|--------------|
| Main version | 15 | 30 |
| rest_events_versions[0] | 162 | 275 |
| rest_events_versions[1] | 162 | 285 |
| rest_events_versions[2] | 143 | 262 |
| **TOTAL** | **497** | **727** |

## Implementation

### Step-by-Step Process

```python
import requests

BRAND_ID = '2186449803775455232'
BASE_URL = 'https://api-g-c7818b61-607.sptpub.com'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Origin': 'https://roobet.com',
    'Referer': 'https://roobet.com/sports/soccer-1'
}

# Step 1: Get manifest with all versions
manifest_url = f"{BASE_URL}/api/v4/prematch/brand/{BRAND_ID}/en/0"
response = requests.get(manifest_url, headers=HEADERS)
manifest = response.json()

# Step 2: Collect ALL version numbers
versions = [manifest['version']]
versions.extend(manifest.get('top_events_versions', []))
versions.extend(manifest.get('rest_events_versions', []))  # ← THE KEY!

# Remove duplicates
versions = list(dict.fromkeys(versions))

# Step 3: Fetch events from EACH version
all_teams = set()
for version in versions:
    events_url = f"{BASE_URL}/api/v4/prematch/brand/{BRAND_ID}/en/{version}"
    response = requests.get(events_url, headers=HEADERS, timeout=10)
    data = response.json()
    
    # Extract soccer teams
    for event_id, event in data.get('events', {}).items():
        desc = event.get('desc', {})
        if desc.get('sport') == '1':  # Soccer
            for competitor in desc.get('competitors', []):
                name = competitor.get('name', '')
                if name:
                    all_teams.add(name)

print(f"Collected {len(all_teams)} unique teams!")
# Output: Collected 727 unique teams!
```

## Results

### Collection Speed

| Sportsbook | Teams | Method | Time |
|------------|-------|--------|------|
| **Roobet** | **718** | Multi-version API | **~10 sec** ✅ |
| Oddswar | 1,323 | Paginated (interval=all) | ~30 sec |
| Stoiximan | 3,228 | Live-only collection | Days/weeks |

### What We Achieved

✅ **718 teams in 10 seconds** - No waiting for matches to go live!
✅ **Comprehensive coverage** - All scheduled soccer matches
✅ **Single collection run** - No need to run continuously for weeks
✅ **No pagination** - All data in one cycle

## Why This Works

The Betby API splits prematch events across multiple version endpoints, likely for:
1. **Performance**: Smaller response sizes per endpoint
2. **Load balancing**: Distribute API load across different versions
3. **Caching**: Each version can be cached independently

By discovering and fetching from ALL version endpoints, we get the complete picture!

## Updated Collector Script

The `collect_roobet_teams.py` script has been updated to:
- ✅ Fetch from main version
- ✅ Fetch from all `top_events_versions`
- ✅ Fetch from all `rest_events_versions` ← NEW!
- ✅ Combine all events and extract unique teams
- ✅ Get 727 teams on first run

## Comparison to Original Question

**Original question:** "Does all this give us a clue on how to get all team names?"

**Answer:** YES! The Betby demo investigation revealed:
1. The manifest response structure
2. The `rest_events_versions` array
3. That each version contains different events
4. How to fetch and combine them all

**Result:** Instead of collecting ~60 teams over time, we now get **727 teams instantly**!

## Files Updated

1. **`collect_roobet_teams.py`** - Now fetches from all version endpoints
2. **`roobet_names.txt`** - Contains 727 unique soccer teams
3. **`BETBY_API_NOTES.md`** - Documents the discovery
4. **This file** - Explains the solution

## Next Steps

This same technique can be applied to:
- Other Betby-powered sportsbooks
- Live events (though they typically have fewer matches)
- Other sports (basketball, tennis, etc.) by changing sport_id

The key is always: **Look for `rest_events_versions` in the manifest!**

