#!/usr/bin/env python3
"""Quick script to check current Hyperliquid positions"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'examples'))

import example_utils
from hyperliquid.info import Info
from hyperliquid.utils.constants import TESTNET_API_URL

# Use same setup as trading bot
wallet_address, info, exchange = example_utils.setup(
    base_url=TESTNET_API_URL,
    skip_ws=True
)

print(f"Wallet: {wallet_address}\n")

# Connect to Hyperliquid
info = Info(TESTNET_API_URL, skip_ws=True)
user_state = info.user_state(wallet_address)

print('=' * 60)
print('CURRENT POSITIONS')
print('=' * 60)

if user_state and 'assetPositions' in user_state:
    positions = user_state['assetPositions']
    if positions:
        for pos in positions:
            coin = pos['position']['coin']
            size = float(pos['position'].get('szi', 0))
            entry_px = float(pos['position'].get('entryPx', 0))
            leverage_val = pos['position'].get('leverage', {})
            leverage = float(leverage_val.get('value', 1)) if isinstance(leverage_val, dict) else 1.0
            notional = abs(size * entry_px)
            margin = notional / leverage if leverage > 0 else notional

            direction = "LONG" if size > 0 else "SHORT"
            print(f"\n{coin} ({direction}):")
            print(f"  Size: {abs(size)}")
            print(f"  Entry: ${entry_px:.2f}")
            print(f"  Leverage: {leverage}x")
            print(f"  Notional: ${notional:.2f}")
            print(f"  Margin: ${margin:.2f}")
    else:
        print("\n❌ No positions found")
else:
    print("\n❌ No positions data")

print('\n' + '=' * 60)
print('ACCOUNT SUMMARY')
print('=' * 60)

if user_state and 'marginSummary' in user_state:
    margin = user_state['marginSummary']
    account_value = float(margin.get('accountValue', 0))
    total_margin = float(margin.get('totalMarginUsed', 0))
    withdrawable = float(margin.get('withdrawable', 0))

    print(f"\nAccount Value: ${account_value:.2f}")
    print(f"Total Margin Used: ${total_margin:.2f}")
    print(f"Available (Withdrawable): ${withdrawable:.2f}")

    if total_margin > 0:
        utilization = (total_margin / account_value * 100) if account_value > 0 else 0
        print(f"Margin Utilization: {utilization:.1f}%")

print('\n' + '=' * 60)
