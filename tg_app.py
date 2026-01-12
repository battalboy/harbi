#!/usr/bin/env python3
"""
Harbi Flask Web Application
Simple web interface for sending Telegram notifications
"""

from flask import Flask, render_template, request, redirect, url_for, flash
import requests
import os

# Flask app configuration
app = Flask(__name__)
app.secret_key = 'harbi_secret_key_change_in_production'  # Change this in production

# Telegram configuration
TELEGRAM_BOT_TOKEN = '8272624197:AAEHXPYrE0E9-hjazYJrcogUTYSH-FM5_SA'

# Test recipients (just James for now)
TEST_RECIPIENTS = [
    (1580648939, 'James')
]

def send_telegram_message(chat_id, message):
    """Send a message to a specific Telegram chat ID"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    try:
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            return True, "Success"
        else:
            error_data = response.json()
            return False, error_data.get('description', f'HTTP {response.status_code}')
            
    except Exception as e:
        return False, str(e)


@app.route('/')
def home():
    """Home page - redirect to tgbot"""
    return redirect(url_for('tgbot'))


@app.route('/results')
def results():
    """Display arbitrage results HTML"""
    import os
    results_file = 'results.html'
    
    # Check if results.html exists
    if not os.path.exists(results_file):
        return "<h1>No results found</h1><p>Run arb_create.py first to generate results.</p>", 404
    
    # Read and return the HTML file
    with open(results_file, 'r', encoding='utf-8') as f:
        return f.read()


@app.route('/tgbot', methods=['GET', 'POST'])
def tgbot():
    """Telegram bot message sender page"""
    if request.method == 'POST':
        message = request.form.get('message', '').strip()
        
        if not message:
            flash('⚠️ Please enter a message', 'warning')
            return redirect(url_for('tgbot'))
        
        # Send to all test recipients
        success_count = 0
        fail_count = 0
        errors = []
        
        for chat_id, name in TEST_RECIPIENTS:
            success, result = send_telegram_message(chat_id, message)
            if success:
                success_count += 1
            else:
                fail_count += 1
                errors.append(f"{name}: {result}")
        
        # Flash results
        if success_count > 0:
            flash(f'✅ Message sent successfully to {success_count} recipient(s)!', 'success')
        
        if fail_count > 0:
            for error in errors:
                flash(f'❌ Failed: {error}', 'error')
        
        return redirect(url_for('tgbot'))
    
    # GET request - show form
    return render_template('tgbot.html', recipients=TEST_RECIPIENTS)


if __name__ == '__main__':
    # Use 0.0.0.0 for remote access, port 5001
    # Set debug=False for production
    print("🚀 Starting Harbi Flask App...")
    print("📱 Telegram Bot Interface: http://localhost:5001/tgbot")
    print("   (or http://89.125.255.32:5001/tgbot on remote server)")
    app.run(host='0.0.0.0', port=5001, debug=True)
