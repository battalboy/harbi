"""
Stake.com Team Name Collector
Uses undetected-chromedriver in HEADLESS mode for remote server compatibility.

Selector discovered: span.ds-body-md-strong.truncate
Runs headless for command-line/SSH environments (remote server: 89.125.255.32)
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
from datetime import datetime

OUTPUT_FILE = "stake_names.txt"

# Major tournament slugs
TOURNAMENT_SLUGS = [
    "england/premier-league",
    "england/championship",
    "england/league-one",
    "spain/laliga",
    "spain/laliga2",
    "germany/bundesliga",
    "germany/2-bundesliga",
    "italy/serie-a",
    "italy/serie-b",
    "france/ligue-1",
    "france/ligue-2",
    "europe/uefa-champions-league",
    "europe/uefa-europa-league",
    "europe/uefa-europa-conference-league",
    "netherlands/eredivisie",
    "portugal/liga-portugal",
    "scotland/premiership",
    "turkey/super-lig",
    "belgium/pro-league",
    "brazil/serie-a",
    "argentina/liga-profesional",
    "usa/mls",
    "mexico/liga-mx",
]

def find_chrome_binary():
    """Find Chrome/Chromium binary on the system."""
    import shutil
    
    # Common Chrome/Chromium binary locations on Linux
    possible_paths = [
        '/usr/bin/google-chrome',
        '/usr/bin/google-chrome-stable',
        '/usr/bin/chromium',
        '/usr/bin/chromium-browser',
        '/snap/bin/chromium',
        shutil.which('google-chrome'),
        shutil.which('google-chrome-stable'),
        shutil.which('chromium'),
        shutil.which('chromium-browser'),
    ]
    
    for path in possible_paths:
        if path and os.path.exists(path):
            return path
    
    return None

def create_driver():
    """Creates undetected ChromeDriver with mobile UA in headless mode."""
    print("🚀 Launching headless browser...")
    
    # Find Chrome binary
    chrome_binary = find_chrome_binary()
    if not chrome_binary:
        print("\n❌ ERROR: Chrome/Chromium not found on this system!")
        print("\n📦 Please install Chrome or Chromium:")
        print("   Ubuntu/Debian: sudo apt-get install chromium-browser")
        print("   or: sudo apt-get install google-chrome-stable")
        print("   CentOS/RHEL: sudo yum install chromium")
        raise RuntimeError("Chrome/Chromium binary not found")
    
    print(f"   ✅ Found Chrome at: {chrome_binary}")
    
    options = uc.ChromeOptions()
    options.binary_location = chrome_binary
    
    mobile_ua = "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.76 Mobile Safari/537.36"
    options.add_argument(f"user-agent={mobile_ua}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # Headless mode (newer version, less detectable)
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    
    driver = uc.Chrome(options=options, version_main=None)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    
    print("✅ Headless browser launched")
    return driver

def accept_cookies(driver):
    """Accept cookies if present."""
    try:
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.variant-action"))
        )
        cookies_btn = driver.find_element(By.CSS_SELECTOR, "button.variant-action")
        cookies_btn.click()
        print("   ✅ Accepted cookies")
        time.sleep(2)
    except:
        pass

def extract_teams(driver):
    """
    Extracts team names using the correct selector: span.ds-body-md-strong.truncate
    Discovered via Browser MCP inspection.
    """
    teams = set()
    
    # Noise to filter out
    IGNORE_LIST = {"Draw", "Hidden", "Winner", "Multi"}
    
    try:
        # Wait for team elements to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "span.ds-body-md-strong.truncate"))
        )
        time.sleep(2)
        
        # Get all team name spans
        team_elements = driver.find_elements(By.CSS_SELECTOR, "span.ds-body-md-strong.truncate")
        
        for element in team_elements:
            try:
                text = element.text.strip()
                
                # Filters:
                if not text or len(text) <= 3 or len(text) >= 50:
                    continue
                
                # Skip UI elements
                if text in IGNORE_LIST or text.startswith("Multi ("):
                    continue
                
                # Skip match names (contain " - " with teams on both sides)
                # But keep team names that have hyphens (e.g., "1. FC Heidenheim 1846")
                if " - " in text:
                    # Check if it looks like "Team1 - Team2" (match name)
                    parts = text.split(" - ")
                    if len(parts) == 2 and len(parts[0]) > 3 and len(parts[1]) > 3:
                        continue  # Likely a match name
                
                teams.add(text)
            except:
                continue
        
        print(f"      📋 Found {len(teams)} teams")
    except Exception as e:
        print(f"      ⚠️  Error: {str(e)}")
    
    return teams

def click_load_more(driver):
    """Clicks Load More button if present."""
    try:
        load_more = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.variant-subtle-link"))
        )
        load_more.click()
        print("      ✅ Clicked 'Load More'")
        time.sleep(3)
        return True
    except:
        return False

def scrape_tournament(driver, slug, is_first=False):
    """Scrapes a single tournament."""
    url = f"https://stake.com/sports/soccer/{slug}"
    print(f"\n   🏆 {slug}")
    
    teams = set()
    
    try:
        # Navigate
        print(f"      🔄 Loading...")
        driver.get(url)
        
        if is_first:
            time.sleep(10)  # Longer wait for first page (Cloudflare)
            accept_cookies(driver)
        else:
            time.sleep(5)  # Shorter for subsequent pages
        
        # Check if redirected to /all (collapsed boxes page)
        current_url = driver.current_url
        if current_url.endswith("/all"):
            print(f"      ⚠️  Redirected to /all (collapsed boxes)")
            print(f"      🔄 Navigating to correct page...")
            
            # Remove /all and try again
            correct_url = current_url.rstrip("/all")
            driver.get(correct_url)
            time.sleep(3)
            
            # Check again
            if driver.current_url.endswith("/all"):
                print(f"      ❌ Still on /all page, skipping...")
                return teams
        
        # Extract teams
        teams.update(extract_teams(driver))
        
        # Try Load More
        if click_load_more(driver):
            teams.update(extract_teams(driver))
    
    except Exception as e:
        print(f"      ❌ Error: {str(e)[:100]}")
    
    print(f"      ✅ Captured {len(teams)} teams")
    return teams

def main():
    print("\n" + "="*70)
    print("🎰 STAKE.COM TEAM NAME COLLECTOR")
    print("="*70)
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Scraping {len(TOURNAMENT_SLUGS)} tournaments")
    print("⚠️  VPN must be connected!")
    print()
    
    all_teams = set()
    driver = None
    
    try:
        driver = create_driver()
        
        for idx, slug in enumerate(TOURNAMENT_SLUGS):
            is_first = (idx == 0)
            teams = scrape_tournament(driver, slug, is_first=is_first)
            all_teams.update(teams)
            
            print(f"\n   📈 Progress: {idx + 1}/{len(TOURNAMENT_SLUGS)}")
            print(f"   📊 Total unique teams: {len(all_teams)}")
            
            time.sleep(2)
        
        # Load existing teams from file (if exists)
        existing_teams = set()
        if os.path.exists(OUTPUT_FILE):
            print(f"\n📖 Loading existing teams from {OUTPUT_FILE}...")
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                existing_teams = {line.strip() for line in f if line.strip()}
            print(f"   Found {len(existing_teams)} existing teams")
        
        # Merge with newly collected teams
        print(f"   Collected {len(all_teams)} teams in this run")
        all_teams.update(existing_teams)
        
        # Save combined list
        print(f"\n💾 Saving {len(all_teams)} total unique teams to {OUTPUT_FILE}...")
        sorted_teams = sorted(all_teams)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            for team in sorted_teams:
                f.write(f"{team}\n")
        
        new_teams = len(all_teams) - len(existing_teams)
        if new_teams > 0:
            print(f"✅ Saved successfully! ({new_teams} new teams added)")
        else:
            print(f"✅ Saved successfully! (no new teams found)")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted")
        if all_teams:
            # Load existing teams and merge
            existing_teams = set()
            if os.path.exists(OUTPUT_FILE):
                with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                    existing_teams = {line.strip() for line in f if line.strip()}
            
            all_teams.update(existing_teams)
            
            print(f"💾 Saving {len(all_teams)} total teams...")
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                for team in sorted(all_teams):
                    f.write(f"{team}\n")
            print(f"✅ Saved {len(all_teams)} teams")
    
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        if driver:
            print("\n🧹 Closing browser...")
            try:
                driver.quit()
            except:
                pass
        
        print("\n" + "="*70)
        print(f"⏰ Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)

if __name__ == "__main__":
    main()
