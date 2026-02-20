#!/usr/bin/env python3
"""
Harbi Event Fetching Daemon

Continuously fetches live odds from betting sites with randomized intervals.
Reads harbi-config.py for runtime configuration (no restart needed).
"""

import time
import random
import subprocess
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path


# Site script mapping
SITE_SCRIPTS = {
    'oddswar': 'event_create_oddswar.py',
    'roobet': 'event_create_roobet.py',
    'stoiximan': 'event_create_stoiximan.py',
    'tumbet': 'event_create_tumbet.py',
    'stake': 'event_create_stake.py'
}

# Failure tracking
site_failures = {}


def load_config():
    """
    Load configuration from harbi-config.py.
    Uses exec() to dynamically reload config each cycle.
    
    Returns:
        dict: Configuration dictionary with ENABLED_SITES, RUN_ARB_CREATE, etc.
    """
    config = {}
    config_file = Path('harbi-config.py')
    
    if not config_file.exists():
        print(f"⚠️  WARNING: harbi-config.py not found, using defaults")
        return {
            'ENABLED_SITES': ['oddswar', 'roobet', 'tumbet'],
            'RUN_ARB_CREATE': True,
            'NOTIFY_ON_ERROR': False,
            'TELEGRAM_USERS': []
        }
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            exec(f.read(), config)
        
        # Extract only the config variables we need
        return {
            'ENABLED_SITES': config.get('ENABLED_SITES', []),
            'RUN_ARB_CREATE': config.get('RUN_ARB_CREATE', True),
            'NOTIFY_ON_ERROR': config.get('NOTIFY_ON_ERROR', False),
            'TELEGRAM_USERS': config.get('TELEGRAM_USERS', [])
        }
    except Exception as e:
        print(f"❌ ERROR loading config: {e}")
        print(f"   Using defaults")
        return {
            'ENABLED_SITES': ['oddswar', 'roobet', 'tumbet'],
            'RUN_ARB_CREATE': True,
            'NOTIFY_ON_ERROR': False,
            'TELEGRAM_USERS': []
        }


def get_varied_random_interval(cycle_num):
    """
    Get a truly random interval between 3-5 minutes.
    Simple and unpredictable - no patterns to detect.
    
    Args:
        cycle_num: Current cycle number (unused, kept for compatibility)
    
    Returns:
        int: Random interval in seconds (180-300)
    """
    # 3 minutes = 180 seconds
    # 5 minutes = 300 seconds
    # Completely random every time
    return random.randint(180, 300)


def run_script(script_name, site_name):
    """
    Run a Python script and return success status.
    
    Args:
        script_name: Name of script to run (e.g., 'event_create_oddswar.py')
        site_name: Human-readable site name for logging
    
    Returns:
        bool: True if successful, False if failed
    """
    script_path = Path(script_name)
    
    if not script_path.exists():
        print(f"      ⚠️  Script not found: {script_name}")
        return False
    
    try:
        # Get Python interpreter from virtual environment or system
        python_exe = sys.executable
        
        # Run script and capture output
        result = subprocess.run(
            [python_exe, str(script_path)],
            capture_output=True,
            text=True,
            timeout=60  # 1 minute timeout
        )
        
        if result.returncode == 0:
            print(f"      ✅ {site_name} completed successfully")
            return True
        else:
            print(f"      ❌ {site_name} failed (exit code: {result.returncode})")
            if result.stderr:
                # Print first 200 chars of error
                error_preview = result.stderr[:200].replace('\n', ' ')
                print(f"         Error: {error_preview}...")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"      ⏱️  {site_name} timed out (>5 minutes)")
        return False
    except Exception as e:
        print(f"      ❌ {site_name} exception: {str(e)[:100]}")
        return False


def run_cycle(cycle_num):
    """
    Run one complete cycle: fetch events from all enabled sites, then run arb_create.
    
    Args:
        cycle_num: Current cycle number
    
    Returns:
        dict: Results summary
    """
    print(f"\n{'='*80}")
    print(f"CYCLE #{cycle_num} - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"{'='*80}")
    
    # Step 1: Load config
    print("\n📂 Loading configuration from harbi-config.py...")
    config = load_config()
    
    enabled_sites = config['ENABLED_SITES']
    run_arb = config['RUN_ARB_CREATE']
    
    if not enabled_sites:
        print("   ⚠️  No sites enabled in config - skipping cycle")
        return {'sites_run': 0, 'sites_succeeded': 0, 'arb_run': False}
    
    print(f"   ✅ Enabled sites: {', '.join(enabled_sites)}")
    print(f"   ✅ Run arb_create: {run_arb}")
    
    # Step 2: Ensure Oddswar runs first if enabled
    sites_to_run = []
    if 'oddswar' in enabled_sites:
        sites_to_run.append('oddswar')
        sites_to_run.extend([s for s in enabled_sites if s != 'oddswar'])
    else:
        sites_to_run = enabled_sites.copy()
    
    # Step 3: Run site scripts
    print(f"\n📊 Fetching events from {len(sites_to_run)} sites...")
    
    sites_succeeded = 0
    for idx, site in enumerate(sites_to_run, 1):
        script = SITE_SCRIPTS.get(site)
        
        if not script:
            print(f"   {idx}. {site.capitalize()}: ⚠️  No script mapping found")
            continue
        
        print(f"   {idx}. {site.capitalize()}:")
        
        success = run_script(script, site.capitalize())
        
        if success:
            sites_succeeded += 1
            # Reset failure counter on success
            site_failures[site] = 0
        else:
            # Track consecutive failures
            site_failures[site] = site_failures.get(site, 0) + 1
            print(f"         (Consecutive failures: {site_failures[site]})")
    
    # Step 4: Run arb_create.py if configured
    arb_success = False
    if run_arb:
        print(f"\n🔍 Running arbitrage detection...")
        arb_success = run_script('arb_create.py', 'Arb Create')
    else:
        print(f"\n⏭️  Skipping arbitrage detection (disabled in config)")
    
    # Step 5: Summary
    print(f"\n📈 Cycle Summary:")
    print(f"   Sites attempted: {len(sites_to_run)}")
    print(f"   Sites succeeded: {sites_succeeded}")
    print(f"   Sites failed: {len(sites_to_run) - sites_succeeded}")
    print(f"   Arbitrage detection: {'✅ Success' if arb_success else '❌ Failed/Skipped'}")
    
    return {
        'sites_run': len(sites_to_run),
        'sites_succeeded': sites_succeeded,
        'arb_run': run_arb,
        'arb_success': arb_success
    }


def main():
    """Main daemon loop."""
    print("="*80)
    print("HARBI EVENT LOOP DAEMON - STARTED")
    print("="*80)
    print(f"Working directory: {os.getcwd()}")
    print(f"Python: {sys.executable}")
    print("\nPress Ctrl+C to stop\n")
    
    cycle_count = 0
    total_stats = {
        'total_cycles': 0,
        'total_sites_run': 0,
        'total_sites_succeeded': 0,
        'total_arb_runs': 0
    }
    
    try:
        while True:
            cycle_count += 1
            
            # Run cycle
            results = run_cycle(cycle_count)
            
            # Update stats
            total_stats['total_cycles'] += 1
            total_stats['total_sites_run'] += results['sites_run']
            total_stats['total_sites_succeeded'] += results['sites_succeeded']
            if results['arb_run']:
                total_stats['total_arb_runs'] += 1
            
            # Get varied random interval
            interval_seconds = get_varied_random_interval(cycle_count)
            interval_minutes = interval_seconds / 60
            next_time = datetime.utcnow() + timedelta(seconds=interval_seconds)
            
            print(f"\n⏱️  Next cycle in {interval_minutes:.1f} minutes ({interval_seconds} seconds)")
            print(f"   Waiting until: {next_time.strftime('%H:%M:%S')} UTC")
            print(f"{'='*80}\n")
            
            # Wait for random interval
            time.sleep(interval_seconds)
    
    except KeyboardInterrupt:
        print("\n\n" + "="*80)
        print("DAEMON STOPPED BY USER")
        print("="*80)
        print(f"\n📊 Final Statistics:")
        print(f"   Total cycles: {total_stats['total_cycles']}")
        print(f"   Total sites run: {total_stats['total_sites_run']}")
        print(f"   Total sites succeeded: {total_stats['total_sites_succeeded']}")
        print(f"   Total arb runs: {total_stats['total_arb_runs']}")
        
        if site_failures:
            print(f"\n⚠️  Site Failure Summary:")
            for site, failures in site_failures.items():
                if failures > 0:
                    print(f"   {site}: {failures} consecutive failures")
        
        print("\nGoodbye!")
    
    except Exception as e:
        print(f"\n\n❌ FATAL ERROR: {e}")
        print("="*80)
        raise


if __name__ == '__main__':
    main()
