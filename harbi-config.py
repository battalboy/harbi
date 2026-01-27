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
    {'name': 'James', 'id': 1580648939},
    {'name': 'Ismail', 'id': 7530341430},
    {'name': 'Hidden_Tomi', 'id': 588354800},
    {'name': 'Totti', 'id': 5387409105},
    {'name': 'AbelardoZ5', 'id': 977623500},
    {'name': 'cassiolincoln10', 'id': 403609484},
    # {'name': 'Ozan', 'id': 580717381},
]
