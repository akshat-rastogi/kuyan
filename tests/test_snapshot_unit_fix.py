#!/usr/bin/env python3
"""
Test script to verify that snapshots now include the commodity unit from the database.
"""

import sys
from database import Database
from datetime import date

def test_snapshot_unit():
    """Test that snapshots include commodity_unit field"""
    
    print("=" * 70)
    print("Testing Snapshot Unit Fix")
    print("=" * 70)
    
    # Use the main database
    db = Database("kuyan.db")
    
    # Get all snapshot dates
    snapshot_dates = db.get_all_snapshot_dates()
    
    if not snapshot_dates:
        print("\n❌ No snapshots found in database")
        return False
    
    print(f"\n✓ Found {len(snapshot_dates)} snapshot dates")
    
    # Get the most recent snapshot date
    latest_date = max(snapshot_dates)
    print(f"✓ Testing with latest snapshot date: {latest_date}")
    
    # Get snapshots for that date
    snapshots = db.get_snapshots_by_date(date.fromisoformat(latest_date))
    
    if not snapshots:
        print("\n❌ No snapshots found for the latest date")
        return False
    
    print(f"✓ Found {len(snapshots)} snapshots")
    
    # Check for commodity accounts
    commodity_snapshots = [s for s in snapshots if s.get('account_type') == 'Commodity']
    
    if not commodity_snapshots:
        print("\n⚠️  No commodity accounts found in snapshots")
        print("   This is OK if you don't have any commodity accounts")
        return True
    
    print(f"\n✓ Found {len(commodity_snapshots)} commodity account(s)")
    
    # Check each commodity snapshot for the unit field
    all_have_unit = True
    for snapshot in commodity_snapshots:
        account_name = snapshot.get('name', 'Unknown')
        commodity = snapshot.get('commodity', 'Unknown')
        unit = snapshot.get('commodity_unit')
        
        print(f"\n  Account: {account_name}")
        print(f"  Commodity: {commodity}")
        print(f"  Unit from snapshot: {unit}")
        
        if unit:
            print(f"  ✓ Unit field present: '{unit}'")
        else:
            print(f"  ❌ Unit field missing or None")
            all_have_unit = False
    
    print("\n" + "=" * 70)
    if all_have_unit:
        print("✅ SUCCESS: All commodity snapshots have the unit field!")
        print("=" * 70)
        return True
    else:
        print("❌ FAILURE: Some commodity snapshots are missing the unit field")
        print("=" * 70)
        return False

if __name__ == "__main__":
    success = test_snapshot_unit()
    sys.exit(0 if success else 1)

# Made with Bob
