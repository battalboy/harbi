# Error Handling Integration Guide

This document outlines the changes needed to integrate centralized error handling into the Harbi arbitrage system.

## Overview

The error handling system works in 3 parts:
1. **error_handler.py** - Centralized error handling module
2. **event_create_*.py scripts** - Modified to catch errors and write error status files
3. **arb_create.py** - Modified to read error status files and display errors in HTML

## Part 1: error_handler.py (✅ CREATED)

This module provides:
- `get_error_message(error, status_code)` - Convert exceptions to Turkish messages
- `handle_request_error(site_name, error, status_code)` - Return standardized error dict
- `is_ban_indicator(error_type, status_code)` - Check if error indicates IP ban
- `success_response(site_name)` - Return success dict

## Part 2: Modify event_create Scripts

Each `event_create_*.py` script needs to:

### Changes Required:

1. **Import error_handler at top:**
```python
from error_handler import handle_request_error, success_response, is_ban_indicator
```

2. **Add error log file constant:**
```python
# At top of file with other constants
ERROR_LOG_FILE = 'oddswar-error.json'  # Or roobet-error.json, etc.
SITE_NAME = 'Oddswar'  # Or 'Roobet', 'Stoiximan', 'Tumbet'
```

3. **Wrap main API calls in try-except:**
```python
try:
    response = requests.get(url, params=params, headers=headers, timeout=30)
    
    # Check status code
    if response.status_code != 200:
        error_info = handle_request_error(SITE_NAME, Exception(f"HTTP {response.status_code}"), response.status_code)
        
        # Warn if possible ban
        if is_ban_indicator(error_info['error_type'], response.status_code):
            print(f"\n⚠️  WARNING: Possible IP ban detected for {SITE_NAME}!")
            print(f"   {error_info['error_message']}")
        
        # Write error log
        with open(ERROR_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(error_info, f, ensure_ascii=False, indent=2)
        
        # Write empty output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('')
        
        return error_info
    
    # ... rest of parsing logic ...
    
except requests.exceptions.ConnectionError as e:
    error_info = handle_request_error(SITE_NAME, e)
    print(f"❌ {error_info['error_message']}")
    with open(ERROR_LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(error_info, f, ensure_ascii=False, indent=2)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('')
    return error_info

except requests.exceptions.Timeout as e:
    error_info = handle_request_error(SITE_NAME, e)
    print(f"❌ {error_info['error_message']}")
    with open(ERROR_LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(error_info, f, ensure_ascii=False, indent=2)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('')
    return error_info

except json.JSONDecodeError as e:
    error_info = handle_request_error(SITE_NAME, e)
    print(f"❌ {error_info['error_message']}")
    with open(ERROR_LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(error_info, f, ensure_ascii=False, indent=2)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('')
    return error_info

except Exception as e:
    error_info = handle_request_error(SITE_NAME, e)
    print(f"❌ {error_info['error_message']}")
    with open(ERROR_LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(error_info, f, ensure_ascii=False, indent=2)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('')
    return error_info
```

4. **On success, write success status:**
```python
# After successfully writing formatted output file
success_info = success_response(SITE_NAME)
with open(ERROR_LOG_FILE, 'w', encoding='utf-8') as f:
    json.dump(success_info, f, ensure_ascii=False, indent=2)

print(f"✅ Successfully fetched {len(events)} events")
return success_info
```

5. **Update if __name__ == '__main__' block:**
```python
if __name__ == '__main__':
    result = main()
    # Exit with error code if there was an error
    if result and result.get('error', False):
        exit(1)
    else:
        exit(0)
```

### Files to Modify:
- `event_create_oddswar.py` → writes `oddswar-error.json`
- `event_create_roobet.py` → writes `roobet-error.json`
- `event_create_stoiximan.py` → writes `stoiximan-error.json`
- `event_create_tumbet.py` → writes `tumbet-error.json`

## Part 3: Modify arb_create.py

### Changes Required:

1. **Add function to load error status:**
```python
def load_error_status(site_name: str) -> Optional[Dict]:
    """
    Load error status from error log file.
    
    Args:
        site_name: Name of site (lowercase, e.g., 'oddswar', 'roobet')
    
    Returns:
        Error dict if error occurred, None if success or file doesn't exist
    """
    error_file = f"{site_name}-error.json"
    
    try:
        with open(error_file, 'r', encoding='utf-8') as f:
            error_data = json.load(f)
            
            # Return error data if there was an error
            if error_data.get('error', False):
                return error_data
            else:
                return None
    except FileNotFoundError:
        # No error file = assume success (backward compatibility)
        return None
    except Exception as e:
        # If we can't read error file, return generic error
        return {
            'site': site_name.capitalize(),
            'error': True,
            'error_type': 'FileReadError',
            'error_message': f"❌ HATA: Error dosyası okunamadı - {str(e)}"
        }
```

2. **Load error statuses in main():**
```python
def main():
    # ... existing code ...
    
    # Step 2: Load events and check for errors
    print("\n📂 Loading events from formatted files...")
    
    # Load error statuses
    oddswar_error = load_error_status('oddswar')
    roobet_error = load_error_status('roobet')
    stoiximan_error = load_error_status('stoiximan')
    tumbet_error = load_error_status('tumbet')
    
    # Load events (will be empty if there was an error)
    oddswar_events = parse_formatted_file('oddswar-formatted.txt')
    roobet_events = parse_formatted_file('roobet-formatted.txt')
    stoiximan_events = parse_formatted_file('stoiximan-formatted.txt')
    tumbet_events = parse_formatted_file('tumbet-formatted.txt')
    
    # Print status
    if oddswar_error:
        print(f"   ❌ Oddswar: {oddswar_error['error_message']}")
    else:
        print(f"   ✅ Oddswar: {len(oddswar_events)} events")
    
    if roobet_error:
        print(f"   ❌ Roobet: {roobet_error['error_message']}")
    else:
        print(f"   ✅ Roobet: {len(roobet_events)} events")
    
    if stoiximan_error:
        print(f"   ❌ Stoiximan: {stoiximan_error['error_message']}")
    else:
        print(f"   ✅ Stoiximan: {len(stoiximan_events)} events")
    
    if tumbet_error:
        print(f"   ❌ Tumbet: {tumbet_error['error_message']}")
    else:
        print(f"   ✅ Tumbet: {len(tumbet_events)} events")
    
    # ... rest of matching logic ...
```

3. **Pass error statuses to generate_html():**
```python
# Update function signature
def generate_html(matched_events: List[Dict], output_file: str = 'results.html', 
                  error_statuses: Dict[str, Optional[Dict]] = None):
    """
    Generate HTML file with matched events in table format.
    
    Args:
        matched_events: List of dicts containing event data and matches
        output_file: Path to output HTML file
        error_statuses: Dict of error statuses {'oddswar': error_dict, 'roobet': error_dict, ...}
    """
    if error_statuses is None:
        error_statuses = {}
    
    # ... existing HTML generation code ...
```

4. **Modify HTML generation to show errors:**
```python
# In generate_html(), when adding site rows:

# Oddswar row (always shown - it's the master)
oddswar = event['oddswar']
if error_statuses.get('oddswar'):
    # Show error instead of odds
    error_msg = error_statuses['oddswar']['error_message']
    html += f"""            <tr>
                <td colspan="4" style="text-align: center; vertical-align: middle; background-color: #fff3cd; color: #856404; padding: 20px;">
                    {error_msg}
                </td>
            </tr>
"""
else:
    # Normal odds row
    html += f"""            <tr>
                <td class="site-name"><a href="{oddswar['link']}" target="_blank">Oddswar oranları</a></td>
                <td>{oddswar['odds_1']}</td>
                <td>{oddswar['odds_x']}</td>
                <td>{oddswar['odds_2']}</td>
            </tr>
"""

# Tumbet row (if matched)
if 'tumbet' in event:
    if error_statuses.get('tumbet'):
        # Show error
        error_msg = error_statuses['tumbet']['error_message']
        html += f"""            <tr>
                <td colspan="4" style="text-align: center; vertical-align: middle; background-color: #fff3cd; color: #856404; padding: 20px;">
                    {error_msg}
                </td>
            </tr>
"""
    else:
        # Normal odds row with arbitrage highlighting
        tumbet = event['tumbet']
        try:
            odds_1_class = ' class="arb-opportunity"' if float(tumbet['odds_1']) > float(oddswar['odds_1']) else ''
            odds_x_class = ' class="arb-opportunity"' if float(tumbet['odds_x']) > float(oddswar['odds_x']) else ''
            odds_2_class = ' class="arb-opportunity"' if float(tumbet['odds_2']) > float(oddswar['odds_2']) else ''
        except (ValueError, KeyError):
            odds_1_class = odds_x_class = odds_2_class = ''
        
        html += f"""            <tr>
                <td class="site-name"><a href="{tumbet['link']}" target="_blank">Tumbet oranları</a></td>
                <td{odds_1_class}>{tumbet['odds_1']}</td>
                <td{odds_x_class}>{tumbet['odds_x']}</td>
                <td{odds_2_class}>{tumbet['odds_2']}</td>
            </tr>
"""

# Similar logic for Stoiximan and Roobet...
```

5. **Update generate_html() call in main():**
```python
# Pass error statuses to HTML generator
error_statuses = {
    'oddswar': oddswar_error,
    'roobet': roobet_error,
    'stoiximan': stoiximan_error,
    'tumbet': tumbet_error
}

generate_html(matched_events, 'results.html', error_statuses)
```

## Testing Strategy

1. **Test with all sites working:**
   - Run all event_create scripts
   - Verify `*-error.json` files show `"error": false`
   - Run arb_create.py
   - Verify results.html shows odds normally

2. **Test with simulated errors:**
   - Manually create error JSON file:
     ```json
     {
       "site": "Oddswar",
       "error": true,
       "error_type": "HTTP_503",
       "error_message": "❌ HATA 503: Servis şu anda kullanılamıyor. Site bakımda veya aşırı yüklü olabilir."
     }
     ```
   - Run arb_create.py
   - Verify error message appears in merged cell in results.html

3. **Test with network errors:**
   - Disconnect internet or block a site
   - Run event_create script
   - Verify proper error message in JSON and console
   - Run arb_create.py
   - Verify error displays in HTML

## Benefits

1. ✅ **Centralized error messages** - All Turkish messages in one place
2. ✅ **Consistent error handling** - Same pattern across all scripts
3. ✅ **IP ban detection** - Warns when 403/429 detected
4. ✅ **User-friendly display** - Errors shown in HTML table
5. ✅ **Debugging info** - Technical details logged to JSON
6. ✅ **Backward compatible** - Works if error files don't exist

## Next Steps

1. ✅ Create error_handler.py (DONE)
2. ⏳ Modify event_create_oddswar.py
3. ⏳ Modify event_create_roobet.py
4. ⏳ Modify event_create_stoiximan.py
5. ⏳ Modify event_create_tumbet.py
6. ⏳ Modify arb_create.py
7. ⏳ Test with all scenarios
8. ⏳ Update event_create_all.py to handle errors
