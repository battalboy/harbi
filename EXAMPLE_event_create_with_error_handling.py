"""
Example implementation showing how to integrate error_handler.py into event_create scripts.

This demonstrates the pattern that should be applied to:
- event_create_oddswar.py
- event_create_roobet.py
- event_create_stoiximan.py
- event_create_tumbet.py
"""

import json
import requests
from error_handler import handle_request_error, success_response, is_ban_indicator


def main():
    """
    Main execution function with error handling.
    Returns error status for arb_create.py to handle.
    """
    site_name = "Oddswar"  # Or "Roobet", "Stoiximan", "Tumbet"
    output_file = "oddswar-formatted.txt"
    error_log_file = "oddswar-error.json"
    
    try:
        print(f"Fetching {site_name} matches...")
        
        # Your existing API call code here
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
        # Check HTTP status code
        if response.status_code != 200:
            error_info = handle_request_error(site_name, Exception(f"HTTP {response.status_code}"), response.status_code)
            
            # Check if this might be a ban
            if is_ban_indicator(error_info['error_type'], response.status_code):
                print(f"\n⚠️  WARNING: Possible IP ban detected for {site_name}!")
                print(f"   Error: {error_info['error_message']}")
                print(f"   Consider stopping all requests and waiting before retrying.")
            
            # Write error to JSON file for arb_create.py to read
            with open(error_log_file, 'w', encoding='utf-8') as f:
                json.dump(error_info, f, ensure_ascii=False, indent=2)
            
            # Still create empty formatted file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('')
            
            return error_info
        
        # Parse response
        data = response.json()
        
        # ... rest of your parsing logic ...
        
        # Write formatted output
        with open(output_file, 'w', encoding='utf-8') as f:
            for event in events:
                f.write(format_event(event) + '\n')
        
        # Write success status
        success_info = success_response(site_name)
        with open(error_log_file, 'w', encoding='utf-8') as f:
            json.dump(success_info, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Successfully fetched {len(events)} events")
        return success_info
        
    except requests.exceptions.ConnectionError as e:
        error_info = handle_request_error(site_name, e)
        print(f"❌ Connection error: {error_info['error_message']}")
        
        with open(error_log_file, 'w', encoding='utf-8') as f:
            json.dump(error_info, f, ensure_ascii=False, indent=2)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('')
        
        return error_info
        
    except requests.exceptions.Timeout as e:
        error_info = handle_request_error(site_name, e)
        print(f"❌ Timeout error: {error_info['error_message']}")
        
        with open(error_log_file, 'w', encoding='utf-8') as f:
            json.dump(error_info, f, ensure_ascii=False, indent=2)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('')
        
        return error_info
        
    except json.JSONDecodeError as e:
        error_info = handle_request_error(site_name, e)
        print(f"❌ JSON parse error: {error_info['error_message']}")
        
        with open(error_log_file, 'w', encoding='utf-8') as f:
            json.dump(error_info, f, ensure_ascii=False, indent=2)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('')
        
        return error_info
        
    except Exception as e:
        error_info = handle_request_error(site_name, e)
        print(f"❌ Unexpected error: {error_info['error_message']}")
        
        with open(error_log_file, 'w', encoding='utf-8') as f:
            json.dump(error_info, f, ensure_ascii=False, indent=2)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('')
        
        return error_info


if __name__ == '__main__':
    result = main()
    # Exit with error code if there was an error
    if result.get('error', False):
        exit(1)
    else:
        exit(0)
