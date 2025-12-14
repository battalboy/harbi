#!/bin/bash
# SSL Environment Setup Script
# Source this file to set SSL environment variables
# Usage: source setup_ssl_env.sh

# Activate virtual environment if not already activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Set SSL certificate environment variables
export SSL_CERT_FILE=$(python -c 'import certifi; print(certifi.where())')
export REQUESTS_CA_BUNDLE=$(python -c 'import certifi; print(certifi.where())')

echo "✅ SSL environment variables set:"
echo "   SSL_CERT_FILE=$SSL_CERT_FILE"
echo "   REQUESTS_CA_BUNDLE=$REQUESTS_CA_BUNDLE"


