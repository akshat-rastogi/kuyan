#!/usr/bin/env python3
"""
KUYAN - Sandbox Database Creator
Create a sandbox database with sample data for KUYAN
This database will be used for the /sandbox URL

Licensed under MIT License - see LICENSE file for details
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import database module
sys.path.insert(0, str(Path(__file__).parent))

from database import Database

SANDBOX_DB = "kuyan-sandbox.db"

def create_sandbox_database():
    """Create a fresh sandbox database with sample data"""
    # Remove existing sandbox database if it exists
    if os.path.exists(SANDBOX_DB):
        os.remove(SANDBOX_DB)
        print(f"Removed existing {SANDBOX_DB}")

    # Create new database and seed with sample data
    print(f"Creating {SANDBOX_DB}...")
    db = Database(db_path=SANDBOX_DB)

    print("Seeding sample data...")
    db.seed_sample_data()

    print(f"✅ Sandbox database created successfully: {SANDBOX_DB}")
    print(f"   - 2 owners (Me, Wife)")
    print(f"   - 4 accounts")
    print(f"   - 24 months of realistic snapshots (Jan of previous year + 24 months)")
    print(f"   - Includes seasonal patterns, market volatility, and realistic variations")

if __name__ == "__main__":
    create_sandbox_database()
