#!/usr/bin/env python3
"""
Run all event creation scripts sequentially.

Executes the four event parsers to fetch and format matches from all betting sites:
- Oddswar (betting exchange)
- Roobet (traditional bookmaker)
- Stoiximan (traditional bookmaker)
- Tumbet (traditional bookmaker)

Each script fetches live and/or upcoming matches and saves them to formatted text files.
"""

import subprocess
import sys
from pathlib import Path
import time


def run_script(script_name: str, description: str) -> tuple[bool, float]:
    """
    Run a Python script and return success status and execution time.
    
    Args:
        script_name: Name of the script file (e.g., 'event_create_oddswar.py')
        description: Human-readable description (e.g., 'Oddswar')
    
    Returns:
        Tuple of (success: bool, execution_time: float)
    """
    print("\n" + "="*80)
    print(f"📡 FETCHING EVENTS FROM {description.upper()}")
    print("="*80)
    
    start_time = time.time()
    
    try:
        # Run the script using the same Python interpreter
        result = subprocess.run(
            [sys.executable, script_name],
            cwd=Path(__file__).parent,
            check=True,
            text=True
        )
        
        elapsed = time.time() - start_time
        print(f"\n✅ {description} completed successfully in {elapsed:.1f}s")
        return True, elapsed
        
    except subprocess.CalledProcessError as e:
        elapsed = time.time() - start_time
        print(f"\n❌ {description} failed after {elapsed:.1f}s")
        print(f"   Error code: {e.returncode}")
        return False, elapsed
        
    except FileNotFoundError:
        elapsed = time.time() - start_time
        print(f"\n❌ {description} script not found: {script_name}")
        return False, elapsed
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n❌ {description} encountered an error: {e}")
        return False, elapsed


def main():
    """Execute all event creation scripts in sequence."""
    print("="*80)
    print("HARBI - EVENT DATA COLLECTION")
    print("="*80)
    print("\nFetching live and upcoming matches from all betting sites...")
    print("This will create/update the following files:")
    print("  - oddswar-formatted.txt")
    print("  - roobet-formatted.txt")
    print("  - stoiximan-formatted.txt")
    print("  - tumbet-formatted.txt")
    
    overall_start = time.time()
    
    # Define scripts to run in order
    scripts = [
        ('event_create_oddswar.py', 'Oddswar'),
        ('event_create_roobet.py', 'Roobet'),
        ('event_create_stoiximan.py', 'Stoiximan'),
        ('event_create_tumbet.py', 'Tumbet'),
    ]
    
    results = {}
    
    # Run each script
    for script_name, description in scripts:
        success, elapsed = run_script(script_name, description)
        results[description] = {
            'success': success,
            'time': elapsed
        }
    
    # Print summary
    total_time = time.time() - overall_start
    
    print("\n\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    
    successful = [name for name, result in results.items() if result['success']]
    failed = [name for name, result in results.items() if not result['success']]
    
    print(f"\n✅ Successful: {len(successful)}/{len(scripts)}")
    for name in successful:
        print(f"   - {name}: {results[name]['time']:.1f}s")
    
    if failed:
        print(f"\n❌ Failed: {len(failed)}/{len(scripts)}")
        for name in failed:
            print(f"   - {name}: {results[name]['time']:.1f}s")
    
    print(f"\n⏱️  Total execution time: {total_time:.1f}s")
    
    print("\n📁 Output files created/updated:")
    for script_name, description in scripts:
        output_file = script_name.replace('event_create_', '').replace('.py', '-formatted.txt')
        status = "✅" if results[description]['success'] else "❌"
        print(f"   {status} {output_file}")
    
    print("\n" + "="*80)
    
    if failed:
        print("\n⚠️  Some scripts failed. Check the output above for details.")
        sys.exit(1)
    else:
        print("\n✅ All event data collected successfully!")
        print("   You can now run: python3 arb_create.py")
        sys.exit(0)


if __name__ == '__main__':
    main()

