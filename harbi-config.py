#!/usr/bin/env python3
"""
Runtime Configuration for Harbi Event Fetching Daemon

This file controls which sites are fetched and notification settings.
Changes take effect on the next daemon cycle (no restart required).
Soccer and Basketball are configured separately.
"""

# ============================================================================
# SOCCER CONFIGURATION
# ============================================================================

# Soccer sites to fetch (comment out to disable)
ENABLED_SITES = [
    'oddswar',
    'roobet',
    'stoiximan',
    'tumbet',
    # 'stake',
]

# Run soccer arbitrage detection after each cycle
RUN_ARB_CREATE = True

# ============================================================================
# BASKETBALL CONFIGURATION
# ============================================================================

# Basketball sites to fetch (comment out to disable)
ENABLED_BASKETBALL_SITES = [
    'oddswar',
    'roobet',
    'stoiximan',
    'tumbet',
    # 'stake',
]

# Run basketball arbitrage detection after each cycle
RUN_BASKETBALL_ARB_CREATE = True

# Notification settings (for errors/issues)
NOTIFY_ON_ERROR = False  # Future: enable when notification method decided

# Telegram user notifications (comment out to disable)
# Note: arb_create.py will read harbi-config.py to send arbitrage alerts
TELEGRAM_USERS = [
    {'name': 'xx', 'id': xx},
    {'name': 'xx', 'id': xx},
    {'name': 'xx', 'id': xx},
    {'name': 'xx', 'id': xx},
    {'name': 'xx', 'id': xx},
    {'name': 'xx', 'id': xx},
]
