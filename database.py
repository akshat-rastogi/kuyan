"""
KUYAN - Database Module
Copyright (c) 2025 mycloudcondo inc.
Licensed under MIT License - see LICENSE file for details
"""

import sqlite3
from datetime import date
from typing import List, Dict, Optional
import json
from contextlib import contextmanager


class Database:
    """Handles all SQLite database operations for KUYAN"""

    def __init__(self, db_path: str = "kuyan.db"):
        self.db_path = db_path
        self.init_database()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def init_database(self):
        """Create tables if they don't exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Owners table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS owners (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    owner_type TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Accounts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    owner TEXT NOT NULL,
                    account_type TEXT NOT NULL,
                    currency TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Snapshots table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_date DATE NOT NULL,
                    account_id INTEGER NOT NULL,
                    balance DECIMAL(15,2) NOT NULL,
                    exchange_rates TEXT,
                    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
                )
            """)

            # Create index for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_snapshot_date
                ON snapshots(snapshot_date)
            """)

            # Currencies table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS currencies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT NOT NULL UNIQUE,
                    flag_emoji TEXT NOT NULL,
                    color TEXT NOT NULL,
                    display_order INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Commodities table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS commodities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    symbol TEXT NOT NULL,
                    color TEXT NOT NULL,
                    unit TEXT NOT NULL DEFAULT 'ounce',
                    display_order INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Add unit column if it doesn't exist (for existing databases)
            cursor.execute("PRAGMA table_info(commodities)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'unit' not in columns:
                cursor.execute("ALTER TABLE commodities ADD COLUMN unit TEXT NOT NULL DEFAULT 'ounce'")

            # Mortgage settings table
            # NOTE: No default mortgage data is seeded. Users must configure mortgage manually.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mortgage_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mortgage_name TEXT NOT NULL UNIQUE,
                    lender_name TEXT NOT NULL,
                    loan_amount DECIMAL(15,2) NOT NULL,
                    interest_rate DECIMAL(10,4) NOT NULL,
                    loan_term_years DECIMAL(10,4) NOT NULL,
                    payments_per_year INTEGER NOT NULL,
                    start_date DATE NOT NULL,
                    recurring_extra_payment DECIMAL(15,2) NOT NULL DEFAULT 0.0,
                    purchase_value DECIMAL(15,2) NOT NULL DEFAULT 0.0,
                    present_value DECIMAL(15,2) NOT NULL DEFAULT 0.0,
                    currency TEXT NOT NULL DEFAULT 'EUR',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Add mortgage_name column if it doesn't exist (for existing databases)
            cursor.execute("PRAGMA table_info(mortgage_settings)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'mortgage_name' not in columns:
                cursor.execute("ALTER TABLE mortgage_settings ADD COLUMN mortgage_name TEXT")
                # Update existing records with a default name
                cursor.execute("UPDATE mortgage_settings SET mortgage_name = 'Primary Mortgage' WHERE mortgage_name IS NULL")
                # Make it NOT NULL after updating
                cursor.execute("""
                    CREATE TABLE mortgage_settings_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        mortgage_name TEXT NOT NULL UNIQUE,
                        lender_name TEXT NOT NULL,
                        loan_amount DECIMAL(15,2) NOT NULL,
                        interest_rate DECIMAL(10,4) NOT NULL,
                        loan_term_years DECIMAL(10,4) NOT NULL,
                        payments_per_year INTEGER NOT NULL,
                        start_date DATE NOT NULL,
                        recurring_extra_payment DECIMAL(15,2) NOT NULL DEFAULT 0.0,
                        purchase_value DECIMAL(15,2) NOT NULL DEFAULT 0.0,
                        present_value DECIMAL(15,2) NOT NULL DEFAULT 0.0,
                        currency TEXT NOT NULL DEFAULT 'EUR',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute("""
                    INSERT INTO mortgage_settings_new
                    SELECT id, mortgage_name, lender_name, loan_amount, interest_rate,
                           loan_term_years, payments_per_year, start_date, recurring_extra_payment,
                           purchase_value, present_value, currency, created_at, updated_at
                    FROM mortgage_settings
                """)
                cursor.execute("DROP TABLE mortgage_settings")
                cursor.execute("ALTER TABLE mortgage_settings_new RENAME TO mortgage_settings")
            
            if 'currency' not in columns:
                cursor.execute("ALTER TABLE mortgage_settings ADD COLUMN currency TEXT NOT NULL DEFAULT 'EUR'")

            # Mortgage extra payments table
            # NOTE: No default extra payments are seeded. Users must configure manually.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mortgage_extra_payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mortgage_id INTEGER NOT NULL,
                    payment_number INTEGER NOT NULL,
                    extra_payment_amount DECIMAL(15,2) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (mortgage_id) REFERENCES mortgage_settings(id) ON DELETE CASCADE
                )
            """)
            
            # Add mortgage_id column if it doesn't exist (for existing databases)
            cursor.execute("PRAGMA table_info(mortgage_extra_payments)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'mortgage_id' not in columns:
                cursor.execute("ALTER TABLE mortgage_extra_payments ADD COLUMN mortgage_id INTEGER")
                # Link existing payments to the first mortgage
                cursor.execute("SELECT id FROM mortgage_settings ORDER BY id LIMIT 1")
                first_mortgage = cursor.fetchone()
                if first_mortgage:
                    cursor.execute("UPDATE mortgage_extra_payments SET mortgage_id = ? WHERE mortgage_id IS NULL", (first_mortgage[0],))

            # Create index for faster queries on mortgage_id and payment number
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_mortgage_payment
                ON mortgage_extra_payments(mortgage_id, payment_number)
            """)

            # Seed default owners if table is empty
            cursor.execute("SELECT COUNT(*) FROM owners")
            if cursor.fetchone()[0] == 0:
                default_owners = [
                    ("Me", "Individual"),
                    ("Wife", "Individual")
                ]
                cursor.executemany(
                    "INSERT INTO owners (name, owner_type) VALUES (?, ?)",
                    default_owners
                )

            # Seed default currencies if table is empty
            cursor.execute("SELECT COUNT(*) FROM currencies")
            if cursor.fetchone()[0] == 0:
                default_currencies = [
                    ("EUR", "🇪🇺", "#003366", 1),  # Navy blue
                    ("USD", "🇺🇸", "#DC143C", 2),  # Crimson red
                    ("INR", "🇮🇳", "#FF8C00", 3)   # Dark orange
                ]
                cursor.executemany(
                    "INSERT INTO currencies (code, flag_emoji, color, display_order) VALUES (?, ?, ?, ?)",
                    default_currencies
                )

            # Seed default commodities if table is empty - Only Gold and Silver
            cursor.execute("SELECT COUNT(*) FROM commodities")
            if cursor.fetchone()[0] == 0:
                default_commodities = [
                    ("Gold", "🥇", "#FFD700", "ounce", 1),    # Gold color
                    ("Silver", "🥈", "#C0C0C0", "ounce", 2),  # Silver color
                ]
                cursor.executemany(
                    "INSERT INTO commodities (name, symbol, color, unit, display_order) VALUES (?, ?, ?, ?, ?)",
                    default_commodities
                )

    # Owner Operations
    def add_owner(self, name: str, owner_type: str) -> int:
        """Add a new owner"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO owners (name, owner_type)
                VALUES (?, ?)
            """, (name, owner_type))
            return cursor.lastrowid

    def get_owners(self) -> List[Dict]:
        """Get all owners"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, owner_type, created_at
                FROM owners
                ORDER BY name
            """)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_owner_names(self) -> List[str]:
        """Get all owner names as a simple list"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM owners ORDER BY name
            """)
            rows = cursor.fetchall()
            return [row[0] for row in rows]

    def update_owner(self, owner_id: int, name: str, owner_type: str):
        """Update an existing owner"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Get old name for updating accounts
            cursor.execute("SELECT name FROM owners WHERE id = ?", (owner_id,))
            old_name = cursor.fetchone()[0]

            # Update owner
            cursor.execute("""
                UPDATE owners
                SET name = ?, owner_type = ?
                WHERE id = ?
            """, (name, owner_type, owner_id))

            # Update all accounts that reference this owner
            cursor.execute("""
                UPDATE accounts
                SET owner = ?
                WHERE owner = ?
            """, (name, old_name))

    def delete_owner(self, owner_id: int) -> bool:
        """Delete an owner (only if no accounts reference it)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Check if any accounts reference this owner
            cursor.execute("SELECT name FROM owners WHERE id = ?", (owner_id,))
            owner_row = cursor.fetchone()
            if not owner_row:
                return False

            owner_name = owner_row[0]
            cursor.execute("""
                SELECT COUNT(*) FROM accounts WHERE owner = ?
            """, (owner_name,))
            count = cursor.fetchone()[0]

            if count > 0:
                return False

            # Safe to delete
            cursor.execute("DELETE FROM owners WHERE id = ?", (owner_id,))
            return True

    def owner_has_accounts(self, owner_name: str) -> bool:
        """Check if an owner has any accounts"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM accounts WHERE owner = ?
            """, (owner_name,))
            count = cursor.fetchone()[0]
            return count > 0

    # Account Operations
    def add_account(self, name: str, owner: str, account_type: str, currency: str, commodity: Optional[str] = None) -> int:
        """Add a new account (currency for Bank/Investment/Other, commodity for Commodity type)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if commodity column exists, if not add it
            cursor.execute("PRAGMA table_info(accounts)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'commodity' not in columns:
                cursor.execute("ALTER TABLE accounts ADD COLUMN commodity TEXT")
            
            cursor.execute("""
                INSERT INTO accounts (name, owner, account_type, currency, commodity)
                VALUES (?, ?, ?, ?, ?)
            """, (name, owner, account_type, currency, commodity))
            return cursor.lastrowid

    def get_accounts(self) -> List[Dict]:
        """Get all accounts"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if commodity column exists
            cursor.execute("PRAGMA table_info(accounts)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'commodity' in columns:
                cursor.execute("""
                    SELECT id, name, owner, account_type, currency, commodity, created_at
                    FROM accounts
                    ORDER BY owner, name
                """)
            else:
                cursor.execute("""
                    SELECT id, name, owner, account_type, currency, created_at
                    FROM accounts
                    ORDER BY owner, name
                """)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def update_account(self, account_id: int, name: str, owner: str, account_type: str, currency: str, commodity: Optional[str] = None):
        """Update an existing account"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if commodity column exists
            cursor.execute("PRAGMA table_info(accounts)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'commodity' in columns:
                cursor.execute("""
                    UPDATE accounts
                    SET name = ?, owner = ?, account_type = ?, currency = ?, commodity = ?
                    WHERE id = ?
                """, (name, owner, account_type, currency, commodity, account_id))
            else:
                cursor.execute("""
                    UPDATE accounts
                    SET name = ?, owner = ?, account_type = ?, currency = ?
                    WHERE id = ?
                """, (name, owner, account_type, currency, account_id))

    def delete_account(self, account_id: int):
        """Delete an account and all its snapshots"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM snapshots WHERE account_id = ?", (account_id,))
            cursor.execute("DELETE FROM accounts WHERE id = ?", (account_id,))

    # Snapshot Operations
    def add_snapshot(self, snapshot_date: date, account_id: int, balance: float, exchange_rates: Dict[str, float]):
        """Add a new snapshot"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO snapshots (snapshot_date, account_id, balance, exchange_rates)
                VALUES (?, ?, ?, ?)
            """, (snapshot_date.isoformat(), account_id, balance, json.dumps(exchange_rates)))
            return cursor.lastrowid

    def get_snapshots_by_date(self, snapshot_date: date) -> List[Dict]:
        """Get all snapshots for a specific date"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if commodity column exists
            cursor.execute("PRAGMA table_info(accounts)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'commodity' in columns:
                cursor.execute("""
                    SELECT s.id, s.snapshot_date, s.account_id, s.balance, s.exchange_rates,
                           a.name, a.owner, a.account_type, a.currency, a.commodity
                    FROM snapshots s
                    JOIN accounts a ON s.account_id = a.id
                    WHERE s.snapshot_date = ?
                    ORDER BY a.owner, a.name
                """, (snapshot_date.isoformat(),))
            else:
                cursor.execute("""
                    SELECT s.id, s.snapshot_date, s.account_id, s.balance, s.exchange_rates,
                           a.name, a.owner, a.account_type, a.currency
                    FROM snapshots s
                    JOIN accounts a ON s.account_id = a.id
                    WHERE s.snapshot_date = ?
                    ORDER BY a.owner, a.name
                """, (snapshot_date.isoformat(),))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_latest_snapshots(self) -> List[Dict]:
        """Get the most recent snapshots for all accounts"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if commodity column exists
            cursor.execute("PRAGMA table_info(accounts)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'commodity' in columns:
                cursor.execute("""
                    SELECT s.id, s.snapshot_date, s.account_id, s.balance, s.exchange_rates,
                           a.name, a.owner, a.account_type, a.currency, a.commodity
                    FROM snapshots s
                    JOIN accounts a ON s.account_id = a.id
                    WHERE s.snapshot_date = (
                        SELECT MAX(snapshot_date) FROM snapshots
                    )
                    ORDER BY a.owner, a.name
                """)
            else:
                cursor.execute("""
                    SELECT s.id, s.snapshot_date, s.account_id, s.balance, s.exchange_rates,
                           a.name, a.owner, a.account_type, a.currency
                    FROM snapshots s
                    JOIN accounts a ON s.account_id = a.id
                    WHERE s.snapshot_date = (
                        SELECT MAX(snapshot_date) FROM snapshots
                    )
                    ORDER BY a.owner, a.name
                """)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_all_snapshot_dates(self) -> List[str]:
        """Get all unique snapshot dates"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT snapshot_date
                FROM snapshots
                ORDER BY snapshot_date DESC
            """)
            rows = cursor.fetchall()
            return [row[0] for row in rows]

    def delete_snapshot(self, snapshot_id: int):
        """Delete a specific snapshot"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM snapshots WHERE id = ?", (snapshot_id,))

    def delete_snapshots_by_date(self, snapshot_date: date):
        """Delete all snapshots for a specific date"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM snapshots WHERE snapshot_date = ?", (snapshot_date.isoformat(),))

    def snapshot_exists_for_date(self, snapshot_date: date) -> bool:
        """Check if any snapshots exist for a given date"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM snapshots WHERE snapshot_date = ?
            """, (snapshot_date.isoformat(),))
            count = cursor.fetchone()[0]
            return count > 0

    # Utility Methods
    def seed_sample_data(self):
        """Add sample data for testing - 2 years of realistic data ending last month"""
        import random
        from currencyConverter import CurrencyConverter
        from datetime import datetime
        from dateutil.relativedelta import relativedelta

        account1_id = self.add_account("TD Chequing", "Me", "Bank", "EUR")
        account2_id = self.add_account("Wealthsimple TFSA", "Me", "Investment", "EUR")
        account3_id = self.add_account("Chase Savings", "Wife", "Bank", "USD")
        account4_id = self.add_account("SBI Account", "Wife", "Bank", "INR")

        # Get enabled currencies (will be EUR, USD, INR for seed data)
        enabled_currencies = self.get_currency_codes()
        rates = CurrencyConverter.get_all_cross_rates(enabled_currencies)
        if not rates:
            rates = {"EUR": 1.0, "USD": 0.75, "INR": 60.0}

        td_balance = 3500.0
        tfsa_balance = 18000.0
        chase_balance = 2200.0
        sbi_balance = 120000.0

        # Calculate starting date: January 1st of previous year
        # E.g., Dec 2025 → Jan 2024, Feb 2026 → Jan 2025
        today = datetime.now().date()
        previous_year = today.year - 1
        start_date = date(previous_year, 1, 1)

        for month in range(24):
            snapshot_date = start_date + relativedelta(months=month)

            # TD Chequing: salary minus expenses with variation
            td_balance += random.randint(400, 600)
            td_balance = max(2000, min(6500, td_balance))
            if snapshot_date.month == 12:
                td_balance -= 800
            elif snapshot_date.month in [7, 8]:
                td_balance -= 400

            # TFSA: monthly contribution + growth with volatility
            tfsa_balance += 500 + (tfsa_balance * 0.08 / 12) + random.uniform(-tfsa_balance * 0.03, tfsa_balance * 0.03)
            # Add market volatility at specific months in the cycle (month 2, 9, and 19)
            if month == 2:  # ~3rd month - market dip
                tfsa_balance *= 0.94
            elif month == 9:  # ~10th month - minor correction
                tfsa_balance *= 0.96
            elif month == 19:  # ~20th month - another dip
                tfsa_balance *= 0.95

            # Chase: steady growth with interest
            chase_balance += random.randint(200, 300) + (chase_balance * 0.04 / 12)
            if snapshot_date.month in [5, 11]:
                chase_balance -= 500

            # SBI: deposits with quarterly expenses
            sbi_balance += random.randint(13000, 17000)
            if snapshot_date.month % 3 == 0:
                sbi_balance -= 20000
            if snapshot_date.month == 4:
                sbi_balance -= 10000

            self.add_snapshot(snapshot_date, account1_id, round(td_balance, 2), rates)
            self.add_snapshot(snapshot_date, account2_id, round(tfsa_balance, 2), rates)
            self.add_snapshot(snapshot_date, account3_id, round(chase_balance, 2), rates)
            self.add_snapshot(snapshot_date, account4_id, round(sbi_balance, 2), rates)

    # Currency Operations
    def get_currencies(self) -> List[Dict]:
        """Get all currencies ordered by display_order"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, code, flag_emoji, color, display_order
                FROM currencies
                ORDER BY display_order
            """)
            return [dict(row) for row in cursor.fetchall()]

    def get_currency_codes(self) -> List[str]:
        """Get list of currency codes"""
        currencies = self.get_currencies()
        return [c['code'] for c in currencies]

    def get_currency_by_code(self, code: str) -> Optional[Dict]:
        """Get currency by code"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, code, flag_emoji, color, display_order
                FROM currencies
                WHERE code = ?
            """, (code,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def add_currency(self, code: str, flag_emoji: str, color: str) -> int:
        """Add a new currency"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Get max display_order
            cursor.execute("SELECT MAX(display_order) FROM currencies")
            max_order = cursor.fetchone()[0] or 0

            cursor.execute("""
                INSERT INTO currencies (code, flag_emoji, color, display_order)
                VALUES (?, ?, ?, ?)
            """, (code, flag_emoji, color, max_order + 1))
            return cursor.lastrowid

    def delete_currency(self, currency_id: int) -> bool:
        """Delete a currency if not used by any account"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get currency code
            cursor.execute("SELECT code FROM currencies WHERE id = ?", (currency_id,))
            row = cursor.fetchone()
            if not row:
                return False

            currency_code = row[0]

            # Check if currency is used by any account
            cursor.execute("SELECT COUNT(*) FROM accounts WHERE currency = ?", (currency_code,))
            count = cursor.fetchone()[0]

            if count > 0:
                return False

            cursor.execute("DELETE FROM currencies WHERE id = ?", (currency_id,))
            return True

    def currency_in_use(self, code: str) -> bool:
        """Check if currency is used by any account"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM accounts WHERE currency = ?", (code,))
            return cursor.fetchone()[0] > 0

    def get_currency_count(self) -> int:
        """Get total number of currencies"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM currencies")
            return cursor.fetchone()[0]

    def update_currency_color(self, currency_id: int, new_color: str) -> bool:
        """Update the color of a currency"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE currencies
                SET color = ?
                WHERE id = ?
            """, (new_color, currency_id))
            return cursor.rowcount > 0

    def clear_all_data(self):
        """Clear all data from database (for testing)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM snapshots")
            cursor.execute("DELETE FROM accounts")
            cursor.execute("DELETE FROM owners")
            cursor.execute("DELETE FROM sqlite_sequence")

            # Re-seed default owners
            default_owners = [
                ("Me", "Individual"),
                ("Wife", "Individual")
            ]
            cursor.executemany(
                "INSERT INTO owners (name, owner_type) VALUES (?, ?)",
                default_owners
            )

    # Commodity Operations
    def get_commodities(self) -> List[Dict]:
        """Get all commodities ordered by display_order"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, symbol, color, unit, display_order
                FROM commodities
                ORDER BY display_order
            """)
            return [dict(row) for row in cursor.fetchall()]

    def get_commodity_names(self) -> List[str]:
        """Get list of commodity names"""
        commodities = self.get_commodities()
        return [c['name'] for c in commodities]

    def get_commodity_by_name(self, name: str) -> Optional[Dict]:
        """Get commodity by name"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, symbol, color, unit, display_order
                FROM commodities
                WHERE name = ?
            """, (name,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def add_commodity(self, name: str, symbol: str, color: str, unit: str = "ounce") -> int:
        """Add a new commodity"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Get max display_order
            cursor.execute("SELECT MAX(display_order) FROM commodities")
            max_order = cursor.fetchone()[0] or 0

            cursor.execute("""
                INSERT INTO commodities (name, symbol, color, unit, display_order)
                VALUES (?, ?, ?, ?, ?)
            """, (name, symbol, color, unit, max_order + 1))
            return cursor.lastrowid

    def delete_commodity(self, commodity_id: int) -> bool:
        """Delete a commodity if not used by any account"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get commodity name
            cursor.execute("SELECT name FROM commodities WHERE id = ?", (commodity_id,))
            row = cursor.fetchone()
            if not row:
                return False

            commodity_name = row[0]

            # Check if commodity is used by any account (assuming accounts can have commodities)
            # For now, we'll allow deletion since commodities aren't linked to accounts yet
            cursor.execute("DELETE FROM commodities WHERE id = ?", (commodity_id,))
            return True

    def commodity_in_use(self, name: str) -> bool:
        """Check if commodity is used by any account"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if commodity column exists
            cursor.execute("PRAGMA table_info(accounts)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'commodity' not in columns:
                return False
            
            cursor.execute("SELECT COUNT(*) FROM accounts WHERE commodity = ?", (name,))
            return cursor.fetchone()[0] > 0

    def get_commodity_count(self) -> int:
        """Get total number of commodities"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM commodities")
            return cursor.fetchone()[0]

    def update_commodity_color(self, commodity_id: int, new_color: str) -> bool:
        """Update the color of a commodity"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE commodities
                SET color = ?
                WHERE id = ?
            """, (new_color, commodity_id))
            return cursor.rowcount > 0
    
    def update_commodity_unit(self, commodity_id: int, new_unit: str) -> bool:
        """Update the unit of a commodity"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE commodities
                SET unit = ?
                WHERE id = ?
            """, (new_unit, commodity_id))
            return cursor.rowcount > 0


    # Mortgage Settings Operations
    def get_all_mortgages(self) -> List[Dict]:
        """Get all mortgage settings"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, mortgage_name, lender_name, loan_amount, interest_rate, loan_term_years,
                       payments_per_year, start_date, recurring_extra_payment,
                       purchase_value, present_value, currency, created_at, updated_at
                FROM mortgage_settings
                ORDER BY mortgage_name
            """)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_mortgage_by_id(self, mortgage_id: int) -> Optional[Dict]:
        """Get a specific mortgage by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, mortgage_name, lender_name, loan_amount, interest_rate, loan_term_years,
                       payments_per_year, start_date, recurring_extra_payment,
                       purchase_value, present_value, currency, created_at, updated_at
                FROM mortgage_settings
                WHERE id = ?
            """, (mortgage_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_mortgage_by_name(self, mortgage_name: str) -> Optional[Dict]:
        """Get a specific mortgage by name"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, mortgage_name, lender_name, loan_amount, interest_rate, loan_term_years,
                       payments_per_year, start_date, recurring_extra_payment,
                       purchase_value, present_value, currency, created_at, updated_at
                FROM mortgage_settings
                WHERE mortgage_name = ?
            """, (mortgage_name,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_mortgage_settings(self) -> Optional[Dict]:
        """Get the current mortgage settings (returns the most recent one) - kept for backward compatibility"""
        mortgages = self.get_all_mortgages()
        return mortgages[0] if mortgages else None

    def add_mortgage(self, mortgage_name: str, lender_name: str, loan_amount: float, interest_rate: float,
                     loan_term_years: float, payments_per_year: int, start_date: date,
                     recurring_extra_payment: float = 0.0, purchase_value: float = 0.0,
                     present_value: float = 0.0, currency: str = "EUR") -> int:
        """Add a new mortgage"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO mortgage_settings (mortgage_name, lender_name, loan_amount, interest_rate,
                                               loan_term_years, payments_per_year, start_date,
                                               recurring_extra_payment, purchase_value, present_value, currency)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (mortgage_name, lender_name, loan_amount, interest_rate, loan_term_years,
                  payments_per_year, start_date.isoformat(), recurring_extra_payment,
                  purchase_value, present_value, currency))
            return cursor.lastrowid or 0

    def update_mortgage(self, mortgage_id: int, mortgage_name: str, lender_name: str, loan_amount: float,
                        interest_rate: float, loan_term_years: float, payments_per_year: int, start_date: date,
                        recurring_extra_payment: float = 0.0, purchase_value: float = 0.0,
                        present_value: float = 0.0, currency: str = "EUR"):
        """Update an existing mortgage"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE mortgage_settings
                SET mortgage_name = ?, lender_name = ?, loan_amount = ?, interest_rate = ?,
                    loan_term_years = ?, payments_per_year = ?, start_date = ?,
                    recurring_extra_payment = ?, purchase_value = ?, present_value = ?,
                    currency = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (mortgage_name, lender_name, loan_amount, interest_rate, loan_term_years,
                  payments_per_year, start_date.isoformat(), recurring_extra_payment,
                  purchase_value, present_value, currency, mortgage_id))

    def delete_mortgage(self, mortgage_id: int):
        """Delete a mortgage and all its extra payments"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM mortgage_extra_payments WHERE mortgage_id = ?", (mortgage_id,))
            cursor.execute("DELETE FROM mortgage_settings WHERE id = ?", (mortgage_id,))

    def save_mortgage_settings(self, lender_name: str, loan_amount: float, interest_rate: float,
                               loan_term_years: float, payments_per_year: int, start_date: date,
                               recurring_extra_payment: float = 0.0, purchase_value: float = 0.0,
                               present_value: float = 0.0, currency: str = "EUR") -> int:
        """Save or update mortgage settings - kept for backward compatibility"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if settings already exist
            cursor.execute("SELECT id FROM mortgage_settings ORDER BY id DESC LIMIT 1")
            existing = cursor.fetchone()
            
            if existing:
                # Update existing settings
                cursor.execute("""
                    UPDATE mortgage_settings
                    SET lender_name = ?, loan_amount = ?, interest_rate = ?,
                        loan_term_years = ?, payments_per_year = ?, start_date = ?,
                        recurring_extra_payment = ?, purchase_value = ?, present_value = ?,
                        currency = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (lender_name, loan_amount, interest_rate, loan_term_years,
                      payments_per_year, start_date.isoformat(), recurring_extra_payment,
                      purchase_value, present_value, currency, existing[0]))
                return existing[0]
            else:
                # Insert new settings with default name
                cursor.execute("""
                    INSERT INTO mortgage_settings (mortgage_name, lender_name, loan_amount, interest_rate,
                                                   loan_term_years, payments_per_year, start_date,
                                                   recurring_extra_payment, purchase_value, present_value, currency)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, ("Primary Mortgage", lender_name, loan_amount, interest_rate, loan_term_years,
                      payments_per_year, start_date.isoformat(), recurring_extra_payment,
                      purchase_value, present_value, currency))
                return cursor.lastrowid or 0

    # Mortgage Extra Payments Operations
    def get_mortgage_extra_payments(self, mortgage_id: Optional[int] = None) -> List[Dict]:
        """Get mortgage extra payments for a specific mortgage or all if mortgage_id is None"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if mortgage_id is not None:
                cursor.execute("""
                    SELECT id, mortgage_id, payment_number, extra_payment_amount, created_at
                    FROM mortgage_extra_payments
                    WHERE mortgage_id = ?
                    ORDER BY payment_number
                """, (mortgage_id,))
            else:
                # For backward compatibility, get payments for first mortgage
                cursor.execute("SELECT id FROM mortgage_settings ORDER BY id LIMIT 1")
                first_mortgage = cursor.fetchone()
                if first_mortgage:
                    cursor.execute("""
                        SELECT id, mortgage_id, payment_number, extra_payment_amount, created_at
                        FROM mortgage_extra_payments
                        WHERE mortgage_id = ?
                        ORDER BY payment_number
                    """, (first_mortgage[0],))
                else:
                    return []
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def save_mortgage_extra_payments(self, mortgage_id: int, payments_data: List[Dict]):
        """Save mortgage extra payments for a specific mortgage (replaces all existing payments)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Clear existing payments for this mortgage
            cursor.execute("DELETE FROM mortgage_extra_payments WHERE mortgage_id = ?", (mortgage_id,))
            
            # Insert new payments
            for payment in payments_data:
                cursor.execute("""
                    INSERT INTO mortgage_extra_payments (mortgage_id, payment_number, extra_payment_amount)
                    VALUES (?, ?, ?)
                """, (mortgage_id, payment['payment_number'], payment['extra_payment_amount']))

    def add_mortgage_extra_payment(self, mortgage_id: int, payment_number: int, extra_payment_amount: float) -> int:
        """Add a single mortgage extra payment"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO mortgage_extra_payments (mortgage_id, payment_number, extra_payment_amount)
                VALUES (?, ?, ?)
            """, (mortgage_id, payment_number, extra_payment_amount))
            return cursor.lastrowid or 0

    def delete_mortgage_extra_payment(self, payment_id: int):
        """Delete a specific mortgage extra payment"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM mortgage_extra_payments WHERE id = ?", (payment_id,))

    def clear_mortgage_extra_payments(self, mortgage_id: Optional[int] = None):
        """Clear mortgage extra payments for a specific mortgage or all if mortgage_id is None"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if mortgage_id is not None:
                cursor.execute("DELETE FROM mortgage_extra_payments WHERE mortgage_id = ?", (mortgage_id,))
            else:
                cursor.execute("DELETE FROM mortgage_extra_payments")
