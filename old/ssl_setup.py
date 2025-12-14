"""
SSL Context Setup with Certifi
This script demonstrates how to use certifi for SSL verification
"""

import ssl
import certifi
import urllib.request

def get_ssl_context():
    """
    Create an SSL context using certifi's certificate bundle.
    Returns an SSL context that can be used with urllib, requests, etc.
    """
    return ssl.create_default_context(cafile=certifi.where())

def test_ssl_connection(url="https://www.google.com"):
    """
    Test SSL connection using certifi certificates.
    """
    print(f"Testing SSL connection to {url}...")
    print(f"Using certificate bundle from: {certifi.where()}")
    
    try:
        context = get_ssl_context()
        with urllib.request.urlopen(url, context=context, timeout=10) as response:
            print(f"✅ SSL connection successful!")
            print(f"Status code: {response.status}")
            print(f"Server: {response.headers.get('Server', 'Unknown')}")
            return True
    except Exception as e:
        print(f"❌ SSL connection failed: {e}")
        return False

def display_cert_info():
    """
    Display information about the certifi certificate bundle.
    """
    print("\n" + "="*60)
    print("SSL Certificate Information")
    print("="*60)
    print(f"Certifi version: {certifi.__version__}")
    print(f"CA Bundle location: {certifi.where()}")
    print(f"Certificate bundle exists: {certifi.where() is not None}")
    print("="*60 + "\n")

if __name__ == "__main__":
    display_cert_info()
    
    # Test SSL connection
    test_ssl_connection()
    
    print("\n" + "="*60)
    print("Usage Examples:")
    print("="*60)
    print("\n1. With requests library:")
    print("   import requests")
    print("   import certifi")
    print("   response = requests.get('https://example.com', verify=certifi.where())")
    
    print("\n2. With urllib:")
    print("   import urllib.request")
    print("   import ssl")
    print("   import certifi")
    print("   context = ssl.create_default_context(cafile=certifi.where())")
    print("   urllib.request.urlopen('https://example.com', context=context)")
    
    print("\n3. Set as default environment variable:")
    print("   export SSL_CERT_FILE=$(python -c 'import certifi; print(certifi.where())')")
    print("   export REQUESTS_CA_BUNDLE=$(python -c 'import certifi; print(certifi.where())')")
    print("="*60 + "\n")


