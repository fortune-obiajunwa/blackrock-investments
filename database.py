import sqlite3
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash


DATABASE = "database.db"


# =========================================
# DATABASE CONNECTION
# =========================================

def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row

    return connection


# =========================================
# PROCESS MATURED INVESTMENTS
# =========================================

def process_matured_investments():

    connection = get_db()
    current_time = datetime.now()

    table_check = connection.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name = 'investments'
    """).fetchone()

    if not table_check:
        connection.close()
        return

    active_investments = connection.execute("""
        SELECT *
        FROM investments
        WHERE status = ?
    """, (
        "Active",
    )).fetchall()

    for investment in active_investments:

        maturity_date_value = investment["maturity_date"]

        if not maturity_date_value:
            continue

        try:
            maturity_date = datetime.fromisoformat(
                maturity_date_value
            )

        except (ValueError, TypeError):
            continue

        if current_time >= maturity_date:

            expected_return = investment["expected_return"]

            if expected_return is None:
                expected_return = investment["amount"]

            connection.execute("""
                UPDATE users
                SET balance = balance + ?
                WHERE id = ?
            """, (
                expected_return,
                investment["user_id"]
            ))

            connection.execute("""
                UPDATE investments
                SET status = ?
                WHERE id = ?
            """, (
                "Completed",
                investment["id"]
            ))

            connection.execute("""
                INSERT INTO transactions
                (
                    user_id,
                    type,
                    amount,
                    status,
                    description
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                investment["user_id"],
                "Investment Return",
                expected_return,
                "Completed",
                " investment maturity return"
            ))

    connection.commit()
    connection.close()


# =========================================
# DATABASE INITIALIZATION
# =========================================

def init_db():

    connection = get_db()

    # =========================================
    # USERS TABLE
    # =========================================

    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            full_name TEXT NOT NULL,

            email TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL,

            balance REAL DEFAULT 0,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
    """)

    # =========================================
    # ADD ADMIN COLUMN
    # =========================================

    user_columns = connection.execute("""
        PRAGMA table_info(users)
    """).fetchall()

    column_names = [
        column["name"]
        for column in user_columns
    ]

    if "is_admin" not in column_names:

        connection.execute("""
            ALTER TABLE users
            ADD COLUMN is_admin INTEGER DEFAULT 0
        """)

    # =========================================
    # TRANSACTIONS TABLE
    # =========================================

    connection.execute("""
        CREATE TABLE IF NOT EXISTS transactions (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            type TEXT NOT NULL,

            amount REAL NOT NULL,

            status TEXT DEFAULT 'Completed',

            description TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
            REFERENCES users(id)

        )
    """)

    # =========================================
    # INVESTMENTS TABLE
    # =========================================

    connection.execute("""
        CREATE TABLE IF NOT EXISTS investments (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            plan_name TEXT NOT NULL,

            amount REAL NOT NULL,

            expected_return REAL NOT NULL,

            duration_days INTEGER NOT NULL,

            start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            maturity_date TIMESTAMP NOT NULL,

            status TEXT DEFAULT 'Active',

            FOREIGN KEY (user_id)
            REFERENCES users(id)

        )
    """)

    # =========================================
    # WITHDRAWAL REQUESTS TABLE
    # =========================================

    connection.execute("""
        CREATE TABLE IF NOT EXISTS withdrawal_requests (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            amount REAL NOT NULL,

            status TEXT DEFAULT 'Pending',

            withdrawal_method TEXT,

            bank_name TEXT,

            account_name TEXT,

            account_number TEXT,

            crypto_currency TEXT,

            crypto_network TEXT,

            wallet_address TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            processed_at TIMESTAMP,

            FOREIGN KEY (user_id)
            REFERENCES users(id)

        )
    """)

    # =========================================
    # DEPOSIT REQUESTS TABLE
    # =========================================

    connection.execute("""
        CREATE TABLE IF NOT EXISTS deposit_requests (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            amount REAL NOT NULL,

            status TEXT DEFAULT 'Pending',

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            processed_at TIMESTAMP,

            FOREIGN KEY (user_id)
            REFERENCES users(id)

        )
    """)

    # =========================================
    # CREATE DEMO ADMIN
    # =========================================

    admin_email = "admin@blackrock.local"

    existing_admin = connection.execute("""
        SELECT id
        FROM users
        WHERE email = ?
    """, (
        admin_email,
    )).fetchone()

    if not existing_admin:

        admin_password = generate_password_hash(
            "Admin@12345"
        )

        connection.execute("""
            INSERT INTO users
            (
                full_name,
                email,
                password,
                balance,
                is_admin
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            "BlackRock Administrator",
            admin_email,
            admin_password,
            0,
            1
        ))

    else:

        connection.execute("""
            UPDATE users
            SET is_admin = 1
            WHERE email = ?
        """, (
            admin_email,
        ))

    connection.commit()
    connection.close()


# =========================================
# DATABASE MIGRATION
# =========================================

def migrate_database():

    connection = get_db()

    # =========================================
    # INVESTMENTS
    # =========================================

    investment_columns = connection.execute("""
        PRAGMA table_info(investments)
    """).fetchall()

    investment_column_names = [
        column["name"]
        for column in investment_columns
    ]

    if "plan_name" not in investment_column_names:

        connection.execute("""
            ALTER TABLE investments
            ADD COLUMN plan_name TEXT
        """)

    if "expected_return" not in investment_column_names:

        connection.execute("""
            ALTER TABLE investments
            ADD COLUMN expected_return REAL DEFAULT 0
        """)

    if "duration_days" not in investment_column_names:

        connection.execute("""
            ALTER TABLE investments
            ADD COLUMN duration_days INTEGER DEFAULT 30
        """)

    if "start_date" not in investment_column_names:

        connection.execute("""
            ALTER TABLE investments
            ADD COLUMN start_date TIMESTAMP
        """)

    if "maturity_date" not in investment_column_names:

        connection.execute("""
            ALTER TABLE investments
            ADD COLUMN maturity_date TIMESTAMP
        """)

    if "status" not in investment_column_names:

        connection.execute("""
            ALTER TABLE investments
            ADD COLUMN status TEXT DEFAULT 'Active'
        """)

    # =========================================
    # WITHDRAWAL REQUESTS
    # =========================================

    withdrawal_columns = connection.execute("""
        PRAGMA table_info(withdrawal_requests)
    """).fetchall()

    withdrawal_column_names = [
        column["name"]
        for column in withdrawal_columns
    ]

    if not withdrawal_column_names:

        connection.execute("""
            CREATE TABLE IF NOT EXISTS withdrawal_requests (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                amount REAL NOT NULL,

                status TEXT DEFAULT 'Pending',

                withdrawal_method TEXT,

                bank_name TEXT,

                account_name TEXT,

                account_number TEXT,

                crypto_currency TEXT,

                crypto_network TEXT,

                wallet_address TEXT,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                processed_at TIMESTAMP,

                FOREIGN KEY (user_id)
                REFERENCES users(id)

            )
        """)

    else:

        if "withdrawal_method" not in withdrawal_column_names:

            connection.execute("""
                ALTER TABLE withdrawal_requests
                ADD COLUMN withdrawal_method TEXT
            """)

        if "bank_name" not in withdrawal_column_names:

            connection.execute("""
                ALTER TABLE withdrawal_requests
                ADD COLUMN bank_name TEXT
            """)

        if "account_name" not in withdrawal_column_names:

            connection.execute("""
                ALTER TABLE withdrawal_requests
                ADD COLUMN account_name TEXT
            """)

        if "account_number" not in withdrawal_column_names:

            connection.execute("""
                ALTER TABLE withdrawal_requests
                ADD COLUMN account_number TEXT
            """)

        if "crypto_currency" not in withdrawal_column_names:

            connection.execute("""
                ALTER TABLE withdrawal_requests
                ADD COLUMN crypto_currency TEXT
            """)

        if "crypto_network" not in withdrawal_column_names:

            connection.execute("""
                ALTER TABLE withdrawal_requests
                ADD COLUMN crypto_network TEXT
            """)

        if "wallet_address" not in withdrawal_column_names:

            connection.execute("""
                ALTER TABLE withdrawal_requests
                ADD COLUMN wallet_address TEXT
            """)

    # =========================================
    # DEPOSIT REQUESTS
    # =========================================

    deposit_columns = connection.execute("""
        PRAGMA table_info(deposit_requests)
    """).fetchall()

    deposit_column_names = [
        column["name"]
        for column in deposit_columns
    ]

    # =========================================
    # CREATE DEPOSIT TABLE IF IT DOES NOT EXIST
    # =========================================

    if not deposit_column_names:

        connection.execute("""
            CREATE TABLE IF NOT EXISTS deposit_requests (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                amount REAL NOT NULL,

                currency TEXT DEFAULT 'USD',

                network TEXT,

                wallet_address TEXT,

                reference TEXT,

                status TEXT DEFAULT 'Pending',

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                processed_at TIMESTAMP,

                FOREIGN KEY (user_id)
                REFERENCES users(id)

            )
        """)

    # =========================================
    # MIGRATE EXISTING DEPOSIT TABLE
    # =========================================

    else:

        if "currency" not in deposit_column_names:

            connection.execute("""
                ALTER TABLE deposit_requests
                ADD COLUMN currency TEXT DEFAULT 'USD'
            """)

        if "network" not in deposit_column_names:

            connection.execute("""
                ALTER TABLE deposit_requests
                ADD COLUMN network TEXT
            """)

        if "wallet_address" not in deposit_column_names:

            connection.execute("""
                ALTER TABLE deposit_requests
                ADD COLUMN wallet_address TEXT
            """)

        if "reference" not in deposit_column_names:

            connection.execute("""
                ALTER TABLE deposit_requests
                ADD COLUMN reference TEXT
            """)

    # =========================================
    # RECHECK DEPOSIT COLUMNS
    # =========================================

    deposit_columns = connection.execute("""
        PRAGMA table_info(deposit_requests)
    """).fetchall()

    deposit_column_names = [
        column["name"]
        for column in deposit_columns
    ]

    # =========================================
    # RECHECK INVESTMENT COLUMNS
    # =========================================

    investment_columns = connection.execute("""
        PRAGMA table_info(investments)
    """).fetchall()

    investment_column_names = [
        column["name"]
        for column in investment_columns
    ]

    # =========================================
    # REPAIR OLD INVESTMENTS
    # =========================================

    if (
        "start_date" in investment_column_names
        and "maturity_date" in investment_column_names
    ):

        old_investments = connection.execute("""
            SELECT
                id,
                duration_days,
                start_date,
                maturity_date
            FROM investments
        """).fetchall()

        for investment in old_investments:

            duration_days = investment["duration_days"]

            if not duration_days or duration_days <= 0:
                duration_days = 30

            start_date = investment["start_date"]
            maturity_date = investment["maturity_date"]

            # =========================================
            # MISSING START DATE
            # =========================================

            if not start_date:

                start_datetime = datetime.now()

                start_date = start_datetime.isoformat()

                maturity_datetime = (
                    start_datetime
                    + timedelta(days=duration_days)
                )

                maturity_date = maturity_datetime.isoformat()

                connection.execute("""
                    UPDATE investments
                    SET
                        duration_days = ?,
                        start_date = ?,
                        maturity_date = ?
                    WHERE id = ?
                """, (
                    duration_days,
                    start_date,
                    maturity_date,
                    investment["id"]
                ))

            # =========================================
            # MISSING MATURITY DATE
            # =========================================

            elif not maturity_date:

                try:

                    parsed_start_date = datetime.fromisoformat(
                        start_date
                    )

                except (ValueError, TypeError):

                    parsed_start_date = datetime.now()

                    start_date = parsed_start_date.isoformat()

                maturity_datetime = (
                    parsed_start_date
                    + timedelta(days=duration_days)
                )

                maturity_date = maturity_datetime.isoformat()

                connection.execute("""
                    UPDATE investments
                    SET
                        duration_days = ?,
                        start_date = ?,
                        maturity_date = ?
                    WHERE id = ?
                """, (
                    duration_days,
                    start_date,
                    maturity_date,
                    investment["id"]
                ))

            # =========================================
            # CHECK INVALID DATES
            # =========================================

            else:

                try:

                    datetime.fromisoformat(start_date)
                    datetime.fromisoformat(maturity_date)

                except (ValueError, TypeError):

                    start_datetime = datetime.now()

                    maturity_datetime = (
                        start_datetime
                        + timedelta(days=duration_days)
                    )

                    connection.execute("""
                        UPDATE investments
                        SET
                            duration_days = ?,
                            start_date = ?,
                            maturity_date = ?
                        WHERE id = ?
                    """, (
                        duration_days,
                        start_datetime.isoformat(),
                        maturity_datetime.isoformat(),
                        investment["id"]
                    ))

    # =========================================
    # SAVE CHANGES
    # =========================================

    connection.commit()
    connection.close()