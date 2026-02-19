# Harbi - Arbitrage Betting System

**THIS IS COMMISSIONED CLIENT SOFTWARE - NOT A PERSONAL PROJECT**

- **5-6 paying clients** will use this system
- **Clients are Turkish** - all notifications, error messages, and UI text will eventually be in Turkish
- **Clients need web access from anywhere** (no Python knowledge required)
- **Remote production server**: xx.xx.xx.xx (user@)
- **Clients CANNOT run scripts manually** - must access via web interface or receive Telegram messages
- **Production deployment is the END GOAL**, not just proof-of-concept
- **Web server required**: Flask application for client access (not simple HTTP server)

**EVERY decision must consider: "Will this work for non-technical clients accessing via web?"**

---

## Client Requirements

**This is a commissioned software project.** The client requires that all traditional betting sites included in the project operate at **full capacity**, meaning:

- **Maximum team coverage**: Each traditional betting site must have as many team names collected as possible
- **Balanced coverage**: Having 150 teams for one site while another site has 1,000+ teams is **not acceptable**
- **Quality standard**: All included sites must provide comparable and comprehensive team coverage to maximize arbitrage opportunities
- **CRITICAL: NO LIMITATIONS ACCEPTED**: Limitations are not tolerated. If a site appears limited, investigate deeper to find the proper API solution
- **CRITICAL: NO BROWSER AUTOMATION/SCRAPING**: Browser automation and web scraping are forbidden due to excessive bandwidth costs (50-150 MB per run vs 1-3 MB for APIs)
- **API-ONLY REQUIREMENT**: All data collection MUST use direct API calls. If an API appears unavailable, investigate further - there is always an API solution
- **Implementation priority**: When facing apparent API limitations, the solution is to find the correct comprehensive API endpoint, NOT to use browser automation or accept reduced coverage

**Current Coverage Status (Soccer):**
- Oddswar: ~1,874 teams ✅ (Master key - defines available opportunities)
- Stoiximan: ~3,521 teams ✅ (Excellent coverage - 88.8% match rate)
- Tumbet: ~1,700+ teams ✅ (Excellent coverage - uses comprehensive getheader endpoint)
- Roobet: ~1,545 teams ✅ (Good coverage - ~38% match rate)
- Stake: ~203 teams ⚠️ (Growing - depends on active leagues, browser automation)

**Current Coverage Status (Basketball):**
- Oddswar Basketball: ~1,600+ teams ✅ (Master key - 2-way odds)
- Stoiximan Basketball: ~712 teams ✅ (Excellent coverage - 110 leagues worldwide via comprehensive API)
- Roobet Basketball: ~211 teams ✅ (Good coverage - all version endpoints)
- Tumbet Basketball: ~400 teams ✅ (Excellent coverage - getheader endpoint)

---

## Project Overview

This is **ARBING SOFTWARE**, not betting software. The goal is to identify and exploit odds discrepancies between:
- **Oddswar** (betting exchange - where you can "sell" or lay odds)
- **Stoiximan, Roobet, Stake & Tumbet** (traditional bookmakers - where you "buy" or back odds)

### How Arbitrage Works
1. Find the same event on both exchange and traditional bookmaker
2. Compare odds
3. When there's a profitable spread, "back" on the traditional site and "lay" on Oddswar
4. Profit from the difference with **minimal risk** (not speculative betting)

### Key Distinction
- **Traditional Bookmaker** (Stoiximan/Roobet/Stake/Tumbet): You bet FOR an outcome
- **Betting Exchange** (Oddswar): You can bet AGAINST an outcome (act as the bookmaker)
- **Arbitrage Opportunity**: When backing + laying the same outcome creates guaranteed profit

---

## Core Challenge: Two-Step Standardization

### Key Definitions
- **Team Name**: A single team (e.g., "Manchester United", "Liverpool FC")
- **Event**: When two teams are playing or have an upcoming match (e.g., "Manchester United vs Liverpool")
- **Goal**: Match team names across sites → Match events across sites → Compare odds for arbitrage

### Step 1: Standardize Team Names
The same team has different names across bookmakers.
- Example: "Man United" vs "Manchester United FC" vs "Manchester Utd"
- **Current focus**: Building team name mappings (`stoiximan_matches.csv`, `roobet_matches.csv`, `tumbet_matches.csv`)
- **Tools**: Fuzzy matching with special rules (indicators, diacritics)
- **Purpose**: Enable accurate event matching in Step 2

#### Matching Algorithm Details
The matching system uses **indicator-first filtering** to ensure accurate matches:

**Indicators Extracted:**
- **Age groups**: U19, U20, U21, U23 (youth teams)
- **Gender**: (W) (women's teams)
- **Reserve teams**: II or B (treated as equivalent under 'RESERVE' indicator)

**Matching Rules:**
- Teams are filtered by indicators BEFORE fuzzy matching
- Only teams with EXACT matching indicators can be compared

**Normalization Process:**
- **Diacritics removal**: Ümraniyespor → Umraniyespor, Beşiktaş → Besiktas
- **Case-insensitive**: NEOM Sports Club → neom sports club (for comparison only)
- **Original names preserved**: Output CSVs contain original team names with proper casing

**Fuzzy Matching:**
- Uses `rapidfuzz` library with `fuzz.ratio` scorer
- **Current threshold**: 60% minimum similarity required for a match

#### Team Collection Scripts
- **Oddswar**: `collect_oddswar_teams.py` → outputs `oddswar_names.txt`
  - Sport IDs: Soccer `1`, Tennis `2`, Basketball `7522`
- **Stoiximan**: `collect_stoiximan_teams.py` → outputs `stoiximan_names.txt`
- **Roobet**: `collect_roobet_teams.py` → outputs `roobet_names.txt` (Betby API, Sport IDs: Soccer `1`, Basketball `2`, Tennis `5`)
- **Tumbet**: `collect_tumbet_teams.py` → outputs `tumbet_names.txt` (SportWide API, `/api/sport/getheader` endpoint)
- **Stake**: `collect_stake_teams.py` → outputs `stake_names.txt` (browser automation, no public API)

**Basketball Team Collectors:**
- `collect_oddswar_basketball.py`, `collect_stoiximan_basketball.py`, `collect_roobet_basketball.py`, `collect_tumbet_basketball.py`

#### Team Matching Scripts
- `create_stoiximan_matches_csv.py`, `create_roobet_matches_csv.py`, `create_tumbet_matches_csv.py`
- Basketball: `create_stoiximan_basketball_matches_csv.py`, `create_roobet_basketball_matches_csv.py`, `create_tumbet_basketball_matches_csv.py`

#### Event Creator Scripts
- Soccer: `event_create_oddswar.py`, `event_create_stoiximan.py`, `event_create_roobet.py`, `event_create_tumbet.py`
- Basketball: `event_create_oddswar_basketball.py`, `event_create_stoiximan_basketball.py`, `event_create_roobet_basketball.py`, `event_create_tumbet_basketball.py`
- Output: `*-formatted.txt` files with full match data (teams, odds, dates, links)

#### Collector vs Event Creator (CRITICAL)
- **Collector scripts**: Build team name databases (maximum coverage, `*_names.txt`)
- **Event creator scripts**: Fetch arbitrage-ready matches with odds (`*-formatted.txt`)
- Different purposes - do not confuse

#### Oddswar as Master Key
- **Oddswar team names are the MASTER KEY** for all comparisons
- All matching: **Oddswar ↔ Traditional Site**
- If a team isn't on Oddswar, it won't appear in the software

#### Oddswar as Source of Truth for Event Metadata (Status, League, Start Time)
- **arb_basketball_create.py** uses Oddswar's values for Status, League, and Start Time in its output (HTML, Telegram). **arb_create.py** (soccer) does not yet have this update
- Traditional sites (Stoiximan, Roobet, Tumbet) contribute: **odds and links**. Their Status/League/Start Time fields are **never used** by the arb pipeline
- **Implication**: Don't over-invest in extracting league names or start times from traditional sites. Oddswar defines the event metadata for display. Having these fields on traditional site formatted files is harmless (e.g. for cross-check, debugging) but not required for arbitrage detection

### Step 2: Standardize Event Formats
- Must identify when different formats represent the SAME event
- Requires Step 1 (team name matching) completed first
- Date/time matching used as confidence booster

---

## Workflows

### Team Name Matching Sequence
1. Collect Oddswar teams (master key)
2. Collect Stoiximan, Roobet, Tumbet, Stake teams
3. Run `create_*_matches_csv.py` for each site

### Cross-Check Workflow
- Use `cross-check_*_soccer.py` or `cross-check_*_basketball.py` scripts
- **Prerequisite**: Run `event_create_oddswar*.py` and `event_create_*`.py first to generate fresh formatted files
- Compares Oddswar formatted output with site formatted output
- Outputs to `temp.txt` (soccer) or `temp_basketball.txt` (basketball)
- Manual review required before adding to CSV

**Validation Rules (Review temp.txt):**
- **Rule 1**: Verify BOTH team pairs - if opponents don't match, REJECT entire event
- **Rule 2**: Check team type indicators (U19, U20, (W), II, B) - must match or both have none
- **Rule 3**: Each valid event yields 2 team name mappings (100.0 confidence)

**CSV Update**: Add as Oddswar, Site, 100.0 - or update existing row if found

---

## Arbitrage Detection

- **Soccer**: `arb_create.py` → `results.html` (3-way odds)
- **Basketball**: `arb_basketball_create.py` → `results_basketball.html` (2-way odds)
- Both send Telegram notifications when arbitrage opportunities found
- System does NOT place bets automatically - identifies opportunities for manual execution

---

## Remote Server Information

- **IP Address**: xx.xx.xx.xx
- **Username**: user
- **Operating System**: Ubuntu
- **Python Version**: 3.10.11
- **Location**: xxxx, xxxx
- **SSH**: `ssh user@xx.xx.xx.xx`

## Web Server

- **Port**: xxxx
- **Soccer results**: `http://xx.xx.xx.xx:xxxx/results.html`
- **Basketball results**: `http://xx.xx.xx.xx:xxxx/results_basketball.html`
- Service: `harbi-http-server.service`

## VPN/Proxy (Gluetun)

- Greece (Stoiximan): Port xxxx
- Canada (Stake): Port xxxx
- Config: `docker-greece.yaml`, `docker-canada.yaml`

## Automated Event Fetching

- **Soccer daemon**: `run_event_loop.py` → `harbi-events.service`
- **Basketball daemon**: `run_basketball_event_loop.py` → `harbi-basketball-events.service`
- Config: `harbi-config.py` (ENABLED_SITES, RUN_ARB_CREATE, TELEGRAM_USERS)

---

## Development

- Use `./venv/bin/python3` - project runs in a virtual environment
- Harbi uses Python 3.10+

---

## Outstanding Tasks / TODO

### High Priority
1. **Update Soccer Stoiximan Scripts** - Apply comprehensive API pattern from basketball
2. **Add Status/League/DateTime to Soccer** - Match basketball display features
3. **Find Tumbet Live API** - `/api/live/getlivegames/ot` returns 404

### Medium Priority
1. **Modify CSV Matching Scripts** - Preserve manual entries when Oddswar team not in names file
2. **Create Stake Matching CSV** - `create_stake_matches_csv.py`
