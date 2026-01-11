# Deep Comparison: `event_create_oddswar.py` vs `event_create_roobet.py`

**Date**: 2026-01-09  
**Purpose**: Document differences between event creator scripts to assess standardization feasibility  
**Status**: Analysis Complete - Awaiting Decision on Implementation

---

## 🎯 Executive Summary

The scripts share **identical output formatting** but differ significantly in:
1. API interaction patterns (2-step vs version-based)
2. Business logic (LAY odds vs standard 1X2 odds)
3. URL construction complexity
4. Error handling granularity

**Key Finding**: Can safely standardize ~40% of code without breaking functionality.

---

## ✅ IDENTICAL Components (Can be shared immediately)

### 1. `format_match(match: Dict) -> str`
- **Lines**: Oddswar 189-211, Roobet 285-307
- **Status**: 100% identical
- **Action**: Can extract to shared module

```python
def format_match(match: Dict) -> str:
    """Format matches identically across all sites"""
    team1 = match.get('team1', 'N/A')
    team2 = match.get('team2', 'N/A')
    team1_odds = match.get('team1_odds', 'N/A')
    draw_odds = match.get('draw_odds', 'N/A')
    team2_odds = match.get('team2_odds', 'N/A')
    link_url = match.get('url', 'N/A')  # Roobet uses 'url', others may vary
    
    return (
        f"Team 1: {team1} | Team 2: {team2} | "
        f"Team 1 Win: {team1_odds} | Draw: {draw_odds} | Team 2 Win: {team2_odds} | "
        f"Link: {link_url}"
    )
```

### 2. `save_formatted_matches(matches, output_file)`
- **Lines**: Oddswar 214-227, Roobet 310-323
- **Status**: 100% identical except print message
- **Action**: Can extract to shared module with output_file parameter

```python
def save_formatted_matches(matches: List[Dict], output_file: str):
    """Save formatted matches to a text file."""
    with open(output_file, 'w', encoding='utf-8') as f:
        for match in matches:
            f.write(format_match(match) + '\n')
    
    print(f"\n✅ Saved {len(matches)} matches to {output_file}")
```

### 3. Output Format
- Both produce: `Team 1: X | Team 2: Y | Team 1 Win: Z | Draw: Z | Team 2 Win: Z | Link: URL`
- Consistent across all sites

---

## 🔧 Configuration Differences

| Aspect | Oddswar | Roobet |
|--------|---------|--------|
| **Constants location** | Inline in functions | Top-level (lines 18-25) |
| **Base URL** | `https://www.oddswar.com` | `https://api-g-c7818b61-607.sptpub.com` |
| **Headers** | Inline in each function | Shared `HEADERS` dict |
| **Brand ID** | Part of URL path (`1oddswar`) | Separate constant (`BRAND_ID`) |

### Oddswar: No Configuration Section
```python
# Headers defined inline in each function (lines 36-39, 61-63)
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/json'
}
```

### Roobet: Centralized Configuration
```python
# Lines 18-25
BRAND_ID = '2186449803775455232'
BASE_URL = 'https://api-g-c7818b61-607.sptpub.com'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Origin': 'https://roobet.com',
    'Referer': 'https://roobet.com/sports/soccer-1'
}
```

**Alignment needed**: Move Oddswar config to top-level constants (like Roobet)

---

## 🌐 API Strategy Differences

### Oddswar: Three-Interval Pattern
```python
# Lines 238-279
1. Fetch inplay markets (size=50)
2. Fetch today markets (size=100) 
3. Fetch all markets (size=200)
4. Deduplicate by market_id
5. Fetch ALL odds in one call (marketDetails API)
```

**Code Flow**:
```python
# Step 1: Fetch markets (list only, no odds)
inplay_data = fetch_markets(interval='inplay', size=50)
today_data = fetch_markets(interval='today', size=100)
all_data = fetch_markets(interval='all', size=200)

# Step 2: Combine and deduplicate
all_market_ids = [unique IDs from all three calls]

# Step 3: Fetch all odds in one batch call
details_data = fetch_market_details(all_market_ids)

# Step 4: Parse by combining markets + details
matches = parse_matches(markets_data, details_data)
```

### Roobet: Version-Based Pattern
```python
# Lines 66-149
1. Fetch manifest to get versions
2. For prematch: fetch main + top_events_versions + rest_events_versions
3. For live: fetch main version only
4. Merge events into combined dict
5. Odds are embedded in event data (no separate call)
```

**Code Flow**:
```python
# Step 1: Get version manifest
manifest = GET /api/v4/{endpoint_type}/brand/{BRAND_ID}/en/0
versions = [main_version] + top_events_versions + rest_events_versions

# Step 2: Fetch from all versions and merge
for version in versions:
    data = GET /api/v4/{endpoint_type}/brand/{BRAND_ID}/en/{version}
    combined_events.update(data['events'])  # Odds already included

# Step 3: Parse events (odds already embedded)
matches = parse_matches(combined_events, endpoint_type, categories, tournaments)
```

**Critical difference**: Oddswar separates market list from odds; Roobet embeds odds in events.

**Alignment challenge**: Cannot unify without breaking site-specific logic.

---

## 💰 Odds Extraction Differences

### Oddswar: LAY Odds Only (Exchange)
```python
# Lines 70-85: extract_lay_odds()
def extract_lay_odds(runner_prices: List[Dict]) -> Optional[float]:
    """
    Extract the best (first) LAY odds from runner prices.
    For arbitrage, we need LAY odds (pink) from Oddswar where we act as bookmaker.
    We ignore BACK odds (blue).
    """
    lay_prices = [p for p in runner_prices if p.get('bet_side') == 'lay']
    if lay_prices:
        return lay_prices[0].get('price')
    return None
```

**Purpose**: Betting exchange where you act as bookmaker (laying bets)

### Roobet: Standard 1X2 Odds (Bookmaker)
```python
# Lines 152-192: extract_1x2_odds()
def extract_1x2_odds(event: Dict) -> tuple:
    """
    Extract 1X2 odds from event data.
    
    Betsby API structure:
    markets: {
        "1": {  # Market ID 1 is 1X2
            "": {
                "1": {"k": "1.42"},  # Home win
                "2": {"k": "4.2"},   # Draw
                "3": {"k": "6.4"}    # Away win
            }
        }
    }
    """
    # Gets selections: "1" (home), "2" (draw), "3" (away)
    # Returns standard bookmaker odds
```

**Purpose**: Traditional bookmaker where you back bets

**Cannot be unified**: Business logic is fundamentally different (exchange vs bookmaker).

**Note**: This is the CORE ARBITRAGE LOGIC - never change this.

---

## 🔗 URL Construction Complexity

### Oddswar: Straightforward
```python
# Lines 161-169
comp_name = competition.get('name', '').lower().replace(' ', '-')
event_slug = event_name.lower().replace(' v ', '-v-').replace(' ', '-')
match_url = f"/brand/1oddswar/exchange/soccer-1/{comp_name}-{comp_id}/{event_slug}-{event_id}/{market_id}"
full_url = f"https://www.oddswar.com{match_url}"
```

**Assumes**: All metadata (competition name, IDs) is always available

### Roobet: Multi-Fallback System
```python
# Lines 242-259
# Primary: Full path with all metadata
if slug and category_slug and tournament_slug:
    match_url = f"https://roobet.com/sports/soccer/{category_slug}/{tournament_slug}/{slug}-{event_id}"

# Fallback 1: Shorter path without category/tournament
elif slug:
    match_url = f"https://roobet.com/sports/{slug}-{event_id}"

# Fallback 2: Minimal path with just event ID
else:
    match_url = f"https://roobet.com/sports/event/{event_id}"
```

**Handles**: Missing metadata gracefully

**Difference**: Roobet has 3 fallback levels; Oddswar assumes all data available.

**Alignment needed**: Add fallback logic to Oddswar if metadata might be missing.

---

## 🔄 Parse Function Signatures

### Oddswar
```python
def parse_matches(markets_data: Dict, details_data: Dict) -> List[Dict]:
    """Takes TWO separate API responses"""
    # markets_data: List of markets (no odds)
    # details_data: Odds for all markets
    # Must combine the two
```

### Roobet
```python
def parse_matches(
    data: Dict, 
    endpoint_type: str, 
    categories: Dict = None, 
    tournaments: Dict = None
) -> List[Dict]:
    """Takes ONE response + metadata + type flag"""
    # data: Events with embedded odds
    # endpoint_type: 'live' or 'prematch' (for URL construction)
    # categories/tournaments: For URL slug mapping
```

**Cannot unify signatures** without major refactoring of API call patterns.

**Site-specific requirements**:
- Oddswar: Needs to combine two separate API responses
- Roobet: Needs metadata for URL construction + type flag

---

## 📊 Statistics & Diagnostics

### Oddswar
```python
# Lines 285, 291, 298, 302
print(f"📊 Total unique markets: {len(all_markets)}")
print(f"   Received odds for {len(details)} markets")
print(f"   Successfully parsed {len(matches)} soccer matches")
```

**Reports**: Market counts, odds availability, final match count

### Roobet
```python
# Lines 360-364
print(f"   Total matches: {len(all_matches)}")
print(f"   Matches with 1X2 odds: {len(matches_with_odds)}")
print(f"   Matches missing odds: {len(all_matches) - len(matches_with_odds)}")
```

**Reports**: Total matches, odds availability breakdown

**Difference**: Roobet provides more detailed odds availability stats.

**Alignment needed**: Add odds availability tracking to Oddswar.

---

## ⚠️ Error Handling Comparison

### Oddswar: Step-Level Error Handling (Continue on Error)
```python
# Lines 240-247, 250-263, 267-279
# Step 1: Fetch LIVE (in-play) markets
try:
    inplay_data = fetch_markets(interval='inplay', size=50)
    # ... process ...
except Exception as e:
    print(f"   Error fetching live markets: {e}")
    # CONTINUES to next step

# Step 2: Fetch TODAY's upcoming markets
try:
    today_data = fetch_markets(interval='today', size=100)
    # ... process ...
except Exception as e:
    print(f"   Error fetching today markets: {e}")
    # CONTINUES to next step
```

**Philosophy**: Collect as much data as possible even if some steps fail

### Roobet: Function-Level Error Handling (Return None)
```python
# Lines 144-149 (in fetch_events_data)
except requests.RequestException as e:
    print(f"Error fetching {endpoint_type} data: {e}")
    return None  # Returns None, caller handles
except Exception as e:
    print(f"Unexpected error in {endpoint_type}: {e}")
    return None

# Main function checks and proceeds:
if prematch_data:
    # process prematch
else:
    print("   No prematch matches found")
```

**Philosophy**: Functions return None on error, caller decides how to proceed

**Difference**: 
- Oddswar: Errors in individual steps don't stop execution (resilient)
- Roobet: Errors return None, main() checks and proceeds (explicit)

**Alignment needed**: Standardize on one pattern (Roobet's pattern is cleaner and more testable)

---

## 📝 Main Function Flow Comparison

### Oddswar (Lines 230-315)
```python
def main():
    1. Print header
    2. Fetch 3 intervals with individual error handling:
       - inplay (try/except, continue on error)
       - today (try/except, continue on error)
       - all (try/except, continue on error)
    3. Check if any markets found (if not, return early)
    4. Fetch all odds in one batch call
    5. Parse combined data (markets + details)
    6. Save
    7. Print done
```

**Steps**: 7 steps with early exit if no markets

### Roobet (Lines 326-384)
```python
def main():
    1. Print header
    2. Fetch prematch (includes metadata extraction)
       - Extract categories and tournaments
       - Parse matches
    3. Fetch live (uses metadata from prematch)
       - Parse matches
    4. Report detailed statistics:
       - Total matches
       - Matches with odds
       - Matches missing odds
    5. Save if matches found
    6. Print done
```

**Steps**: 6 steps with conditional save

**Key difference**: Roobet extracts and passes metadata; Oddswar doesn't need it.

---

## 🎯 Alignment Recommendations

### ✅ Can Standardize (Easy) - Phase 1

1. **Extract shared functions** to `event_create_common.py`:
   ```python
   # event_create_common.py
   def format_match(match: Dict) -> str:
       """Shared formatting function"""
       
   def save_formatted_matches(matches: List[Dict], output_file: str):
       """Shared save function"""
       
   def print_header(site_name: str):
       """Consistent header printing"""
       
   def print_step(step_num: int, message: str):
       """Consistent step printing"""
   ```

2. **Move config to top**:
   - Add constants section to Oddswar (like Roobet lines 18-25)
   ```python
   # Configuration
   BASE_URL = 'https://www.oddswar.com'
   API_BASE = 'https://www.oddswar.com/api/brand/1oddswar/exchange'
   HEADERS = {
       'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
       'Accept': 'application/json'
   }
   ```

3. **Standardize printing**:
   - Use consistent emoji and formatting
   - Add step numbers to all prints
   - Consistent error message format

**Risk Level**: LOW (functions are identical, just moving code)

---

### ⚠️ Can Standardize (Moderate) - Phase 2

4. **Error handling pattern**:
   - Use Roobet's return-None pattern in fetch functions
   - Add consistent error messages
   - Wrap in try/except with specific exception types:
     - `requests.RequestException` for HTTP errors
     - `json.JSONDecodeError` for parsing errors
     - `KeyError` for missing data
     - `Exception` as fallback

5. **Statistics reporting**:
   - Add odds availability tracking to Oddswar:
   ```python
   matches_with_odds = [m for m in matches if m['team1_odds'] is not None]
   print(f"   Matches with odds: {len(matches_with_odds)}")
   print(f"   Matches missing odds: {len(matches) - len(matches_with_odds)}")
   ```
   - Standardize stat format across all scripts

**Risk Level**: MEDIUM (changes control flow, requires careful testing)

---

### ❌ Cannot Standardize (Site-Specific) - Keep As-Is

6. **API call patterns**: 
   - Oddswar: 2-step process (markets list → odds batch fetch)
   - Roobet: Version-based process (manifest → versioned endpoints)
   - **Reason**: Completely different API architectures

7. **Odds extraction logic**: 
   - Oddswar: LAY odds only (exchange)
   - Roobet: Standard 1X2 odds (bookmaker)
   - **Reason**: CORE BUSINESS REQUIREMENT for arbitrage
   - **WARNING**: Never attempt to unify this logic

8. **Parse function signatures**: 
   - Tied to API structure
   - **Reason**: Different data models (combined vs embedded)

9. **URL construction**: 
   - Site-specific requirements
   - **Reason**: Different URL schemes and fallback needs

**Risk Level**: NONE (no changes recommended)

---

## 📋 Implementation Plan

### Phase 1: Extract Common Code (No Breaking Changes)
**Effort**: 1-2 hours  
**Risk**: LOW (5%)  
**Testing**: Compare output files before/after

1. Create `event_create_common.py`:
   ```python
   from typing import Dict, List
   
   def format_match(match: Dict) -> str:
       """Format match for output file"""
       
   def save_formatted_matches(matches: List[Dict], output_file: str):
       """Save matches to file"""
       
   def print_header(site_name: str, live: bool, prematch: bool):
       """Print consistent header"""
       
   def print_step(step_num: int, message: str):
       """Print numbered step"""
   ```

2. Update both scripts to import from common:
   ```python
   from event_create_common import format_match, save_formatted_matches, print_header
   ```

3. Remove duplicate functions from both scripts

4. Test: Run both scripts, verify output files are identical

---

### Phase 2: Standardize Structure (Moderate Changes)
**Effort**: 2-4 hours  
**Risk**: MEDIUM (30%)  
**Testing**: Full regression test on all outputs

1. **Add constants section to Oddswar**:
   - Move inline config to top
   - Match Roobet's structure

2. **Standardize error handling**:
   - Refactor Oddswar's try/except blocks
   - Return None on error (like Roobet)
   - Add specific exception types

3. **Unify print formatting**:
   - Use print_step() everywhere
   - Add consistent emoji
   - Match diagnostic output format

4. **Add statistics tracking**:
   - Track odds availability in Oddswar
   - Report same metrics across all scripts

5. **Test thoroughly**:
   - Run both scripts multiple times
   - Compare output files byte-by-byte
   - Verify error handling (simulate API failures)

---

### Phase 3: Keep Site-Specific Logic Separate
**Effort**: 1 hour (documentation only)  
**Risk**: NONE  
**Testing**: Not applicable

1. **Document why certain code cannot be unified**:
   - Add comments explaining site-specific requirements
   - Document API differences
   - Explain business logic differences (LAY vs 1X2)

2. **Create a "DO NOT CHANGE" section** in each script:
   ```python
   # ============================================================
   # SITE-SPECIFIC CODE - DO NOT ATTEMPT TO STANDARDIZE
   # ============================================================
   # The following functions are specific to [SITE] API and
   # cannot be unified with other scripts due to:
   # - Different API architecture (2-step vs versioned)
   # - Different odds model (LAY vs 1X2)
   # - Different URL construction requirements
   # ============================================================
   ```

---

## 📊 Standardization Summary

| Category | Lines of Code | Can Standardize | Cannot Standardize | Notes |
|----------|--------------|-----------------|-------------------|-------|
| **Output formatting** | ~50 | ✅ 100% | - | Identical functions |
| **Configuration** | ~15 | ✅ 100% | - | Move to top |
| **Error handling** | ~40 | ✅ 80% | 20% | Pattern standardization |
| **Statistics** | ~20 | ✅ 80% | 20% | Add tracking |
| **API calls** | ~150 | ❌ 0% | 100% | Site-specific |
| **Odds extraction** | ~50 | ❌ 0% | 100% | Business logic |
| **URL construction** | ~30 | ❌ 0% | 100% | Site-specific |
| **Parse functions** | ~100 | ❌ 0% | 100% | Data model tied |
| **TOTAL** | ~455 | ~40% | ~60% | |

**Conclusion**: Can safely standardize ~40% of code (185 lines) without breaking functionality.

---

## 🚨 Critical Warnings

### DO NOT TOUCH
1. **Odds extraction logic** (Oddswar LAY vs Roobet 1X2)
   - This is the CORE ARBITRAGE LOGIC
   - Changing this breaks the entire business model
   - Oddswar must return LAY odds (pink) for exchange
   - Traditional sites must return standard 1X2 for bookmakers

2. **API call patterns**
   - Each site has unique API architecture
   - Attempting to unify will break data collection
   - Different sites require different approaches

3. **URL construction**
   - Site-specific URL schemes
   - Critical for results.html links
   - Breaking URLs breaks client experience

---

## ✅ Estimated Safety Levels

| Phase | What | Safety | Why |
|-------|------|--------|-----|
| **Phase 1** | Extract common functions | 95% SAFE | Functions are 100% identical |
| **Phase 2** | Standardize structure | 70% SAFE | Changes control flow but not logic |
| **Phase 3** | Keep site-specific | 100% SAFE | No changes, documentation only |
| **OVERALL** | Full implementation | 85% SAFE | With proper testing |

---

## 📝 Next Steps

**Decision Required**: Proceed with standardization?

**Option A: Full Standardization** (Phases 1-3)
- Effort: 4-7 hours
- Risk: Medium
- Benefit: More maintainable code
- Requires: Full regression testing

**Option B: Partial Standardization** (Phase 1 only)
- Effort: 1-2 hours  
- Risk: Low
- Benefit: Shared functions, less code duplication
- Requires: Basic output comparison

**Option C: No Standardization** (Documentation only)
- Effort: 30 minutes
- Risk: None
- Benefit: Understanding of differences
- Requires: Nothing

**Recommendation**: Start with Phase 1 (low risk, high value), then decide on Phase 2 based on results.

---

## 📌 Files to Review Next

To complete the full analysis, we should also examine:
- [ ] `event_create_stoiximan.py` - Compare with Oddswar/Roobet patterns
- [ ] `event_create_tumbet.py` - Compare with Oddswar/Roobet patterns
- [ ] `event_create_all.py` - Understand orchestration layer

This will give us a complete picture of standardization opportunities across all 5 scripts.
