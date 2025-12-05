"""
Stealth web scraper for Stoiximan
Fetches live betting data while avoiding bot detection
"""

from playwright.sync_api import sync_playwright
import time
import sys


def fetch_stoiximan_page(url='https://en.stoiximan.gr/live/', output_file='stoiximan-live.html'):
    """
    Fetch Stoiximan page with stealth settings to avoid bot detection.
    
    Args:
        url (str): URL to fetch
        output_file (str): File to save HTML to
    """
    print("Launching browser with stealth settings...")
    
    with sync_playwright() as p:
        # Launch with more realistic settings
        browser = p.chromium.launch(
            headless=False,  # Use headed mode (more realistic)
            args=[
                '--disable-blink-features=AutomationControlled',  # Hide automation
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--no-sandbox',
            ]
        )
        
        # Create context with realistic settings
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            locale='en-GB',
            timezone_id='Europe/Athens',
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-GB,en;q=0.9,el;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0',
            }
        )
        
        # Hide webdriver property
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Override chrome property
            window.chrome = {
                runtime: {}
            };
            
            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
        
        page = context.new_page()
        
        print(f"Navigating to {url}...")
        try:
            # Navigate to page
            page.goto(url, wait_until='networkidle', timeout=30000)
            
            print("Waiting for content to load...")
            time.sleep(5)  # Give time for dynamic content
            
            # Wait for specific element (event cards)
            try:
                page.wait_for_selector('[data-qa="event-card"]', timeout=10000)
                print("✓ Found event cards")
            except:
                print("⚠ Warning: No event cards found yet, but continuing...")
            
            # Scroll to load more content
            print("Scrolling page to load all content...")
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)
            
            # Get HTML
            html_content = page.content()
            
            print(f"Saving HTML to {output_file}...")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Take a screenshot for verification
            screenshot_file = output_file.replace('.html', '.png')
            page.screenshot(path=screenshot_file, full_page=False)
            print(f"Screenshot saved to {screenshot_file}")
            
            print(f"✅ Page saved! ({len(html_content):,} characters)")
            
            # Quick check
            if 'regulatory provisions' in html_content or 'cannot be accessed' in html_content:
                print("\n⚠️  WARNING: Page appears to be geo-blocked!")
                print("Check if VPN is active and connected to a Greek server.")
            elif 'data-qa="event-card"' in html_content or 'event-card' in html_content:
                print("✓ HTML contains match data!")
            else:
                print("\n⚠️  WARNING: HTML may not contain match data.")
                print("Check the screenshot to see what was captured.")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            # Try to save whatever we got
            try:
                html_content = page.content()
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print(f"Partial content saved to {output_file}")
            except:
                pass
        
        finally:
            browser.close()


def main():
    """Main function for command-line usage."""
    url = sys.argv[1] if len(sys.argv) > 1 else 'https://en.stoiximan.gr/live/'
    output = sys.argv[2] if len(sys.argv) > 2 else 'stoiximan-live.html'
    
    print("="*70)
    print("STOIXIMAN STEALTH FETCHER")
    print("="*70)
    print(f"URL: {url}")
    print(f"Output: {output}")
    print()
    
    fetch_stoiximan_page(url, output)
    
    print("\n" + "="*70)
    print("NEXT STEPS:")
    print("="*70)
    print("1. Check the screenshot to verify the page loaded correctly")
    print("2. Run the parser:")
    print(f"   python stoiximan.py {output} stoiximan-formatted.txt")
    print("="*70)


if __name__ == '__main__':
    main()

