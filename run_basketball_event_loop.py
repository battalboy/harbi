#!/usr/bin/env python3
"""
Basketball Event Loop Daemon
Continuously fetches basketball events and runs arbitrage detection
"""

import time
import random
import subprocess
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
log_dir = Path('/home/giray/harbi/logs')
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'basketball_event_loop.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Configuration
ENABLED_SITES = [
    'oddswar',
    'roobet',
    'stoiximan',
    'tumbet'
]

RUN_ARB_CREATE = True


def run_script(script_name: str) -> bool:
    """Run a Python script and return success status."""
    try:
        logger.info(f"Running {script_name}...")
        result = subprocess.run(
            ['python3', script_name],
            cwd='/home/giray/harbi',
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            logger.info(f"✅ {script_name} completed successfully")
            return True
        else:
            logger.error(f"❌ {script_name} failed with code {result.returncode}")
            logger.error(f"Error output: {result.stderr[:500]}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"❌ {script_name} timed out after 120 seconds")
        return False
    except Exception as e:
        logger.error(f"❌ {script_name} error: {str(e)}")
        return False


def run_cycle():
    """Run one complete cycle of basketball event fetching."""
    logger.info("="*80)
    logger.info("STARTING BASKETBALL EVENT FETCH CYCLE")
    logger.info("="*80)
    
    # Always run Oddswar first (master key)
    run_script('event_create_oddswar_basketball.py')
    
    # Run other enabled sites
    for site in ENABLED_SITES:
        if site == 'oddswar':
            continue  # Already ran
        
        script_name = f'event_create_{site}_basketball.py'
        run_script(script_name)
    
    # Run arbitrage detection
    if RUN_ARB_CREATE:
        logger.info("Running basketball arbitrage detection...")
        run_script('arb_basketball_create.py')
    
    logger.info("="*80)
    logger.info("BASKETBALL CYCLE COMPLETE")
    logger.info("="*80)


def get_next_interval():
    """Generate random interval with varied patterns for anti-detection."""
    # Randomly choose between different interval patterns
    pattern = random.choice([
        (120, 240),   # 2-4 minutes
        (180, 360),   # 3-6 minutes
        (240, 480),   # 4-8 minutes
    ])
    
    return random.uniform(pattern[0], pattern[1])


def main():
    """Main event loop."""
    logger.info("🏀 Basketball Event Loop Daemon Started")
    
    cycle_count = 0
    
    try:
        while True:
            cycle_count += 1
            logger.info(f"\n{'='*80}")
            logger.info(f"BASKETBALL CYCLE #{cycle_count}")
            logger.info(f"{'='*80}\n")
            
            # Run the cycle
            run_cycle()
            
            # Calculate next interval
            interval = get_next_interval()
            minutes = interval / 60
            next_time = datetime.now()
            logger.info(f"\n⏱️  Next basketball cycle in {minutes:.1f} minutes")
            logger.info(f"💤 Sleeping...\n")
            
            # Sleep
            time.sleep(interval)
            
    except KeyboardInterrupt:
        logger.info("\n🛑 Basketball Event Loop stopped by user")
    except Exception as e:
        logger.error(f"\n❌ Fatal error in basketball event loop: {str(e)}")
        raise


if __name__ == '__main__':
    main()
