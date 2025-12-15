# Tumbet Integration Summary

## Overview
Successfully integrated **Tumbet797.com** as the third traditional betting site for arbitrage opportunities in the Harbi system.

## API Discovery

### Tumbet Uses SportWide Platform
- **Platform**: SportWide (third-party sportsbook solution)
- **API Domain**: `analytics-sp.googleserv.tech`
- **Brand ID**: `161` (Tumbet's identifier)
- **Language Code**: `ot` (Turkish)

### Key API Endpoints

1. **Sports Header/Categories**
```
https://analytics-sp.googleserv.tech/api/sport/getheader/ot
```

2. **Top Prematch Games** (with game IDs)
```
https://analytics-sp.googleserv.tech/api/prematch/getprematchtopgames/ot
```

3. **Game Details** (with team names)
```
https://analytics-sp.googleserv.tech/api/prematch/getprematchgameall/ot/161/?games=,<game_ids>
```

### Response Structure
The API returns:
- **`game`** array: Game details, odds, markets
- **`teams`** array: Team names with IDs and proper UTF-8 characters
  ```json
  {
    "Sport": 1,
    "ID": 16833,
    "Name": "Fenerbahçe"
  }
  ```

## Implementation

### 1. Team Collection Script
**File**: `collect_tumbet_teams.py`

**Workflow**:
1. Fetch top prematch soccer games (returns game IDs)
2. Request detailed game data with team names
3. Extract team names from `teams` array
4. Merge with existing teams and save to `tumbet_names.txt`

**Initial Results**:
- Collected **149 unique team names** from 88 top games
- Includes proper UTF-8 characters (e.g., "Bayern Münih", "Fenerbahçe")

### 2. Team Matching Script
**File**: `create_tumbet_matches_csv.py`

**Features**:
- Fuzzy matching with `rapidfuzz` (minimum 80% similarity)
- Diacritic normalization for comparison (preserves originals in output)
- Indicator matching rules:
  - Age groups: U19, U20, U21, U23
  - Gender: (W)
  - Reserve teams: II and B (treated as equivalent)
- Uses Oddswar as master key

**Matching Results**:
- **Total Oddswar teams**: 1,424
- **Matched teams**: 125
- **Match rate**: 8.8%
- Output: `tumbet_matches.csv`

## Files Created

### Scripts
1. `collect_tumbet_teams.py` - Collects team names from Tumbet API
2. `create_tumbet_matches_csv.py` - Matches Oddswar ↔ Tumbet team names

### Data Files
1. `tumbet_names.txt` - 149 team names from Tumbet
2. `tumbet_matches.csv` - 1,424 rows (Oddswar ↔ Tumbet mappings with confidence scores)

## Documentation Updates

Updated `.cursorrules` with:
- Added Tumbet to project overview
- Added Tumbet collection script documentation
- Added Tumbet matching script documentation  
- Updated workflow sequence (now 7 steps instead of 5)
- Moved Tumbet from "Future Sites" to active sites
- Updated current status with 8.8% match rate

## Workflow Integration

The complete team matching workflow is now:
1. `collect_oddswar_teams.py` - Collect Oddswar teams (master key)
2. `collect_stoiximan_teams.py` - Collect Stoiximan teams
3. `collect_roobet_teams.py` - Collect Roobet teams
4. `collect_tumbet_teams.py` - **Collect Tumbet teams** ✨ NEW
5. `create_stoiximan_matches_csv.py` - Match Oddswar ↔ Stoiximan
6. `create_roobet_matches_csv.py` - Match Oddswar ↔ Roobet
7. `create_tumbet_matches_csv.py` - **Match Oddswar ↔ Tumbet** ✨ NEW

## Match Rate Comparison

| Site | Match Rate |
|------|-----------|
| Stoiximan | 88.8% |
| Roobet | 26.7% |
| Tumbet | 8.8% |

**Note**: Tumbet's lower match rate is expected because:
- Only collected 149 teams from top prematch games
- Running the collector multiple times will increase coverage
- More games = more teams = higher match rate

## API Access Notes

- **Protection**: Tumbet797.com has Cloudflare protection
- **Access Method**: Works with Turkish IP
- **Browser Access**: Required for initial API discovery
- **Script Access**: Direct API calls work once endpoints are identified

## Next Steps

To improve Tumbet match rate:
1. Run `collect_tumbet_teams.py` multiple times to collect more teams
2. The API shows top games only, so timing matters (different games at different times)
3. Consider fetching from additional API endpoints if available

## Technical Notes

### Similar to Roobet
Both Tumbet and Roobet use third-party sportsbook platforms:
- **Roobet**: Betsby API (`*.sptpub.com`)
- **Tumbet**: SportWide API (`analytics-sp.googleserv.tech`)

### UTF-8 Support
All scripts properly handle international characters:
- Turkish: Fenerbahçe, Beşiktaş, Kasımpaşa
- German: Bayern Münih
- And more...

### Matching Quality
Examples of high-confidence matches (100.0):
- Arsenal → Arsenal
- Barcelona → Barcelona
- Fenerbahce → Fenerbahçe
- Galatasaray → Galatasaray
- Liverpool → Liverpool
- Real Madrid → Real Madrid

## Conclusion

✅ Tumbet successfully integrated as the **third traditional betting site**  
✅ Collection and matching scripts working correctly  
✅ Documentation updated  
✅ Ready for arbitrage opportunity identification (once Step 2 is implemented)

---

**Date**: December 15, 2025  
**Status**: Complete ✨

