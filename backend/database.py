import sqlite3
import os
from threading import Lock

# Database file path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'purchase_slips.db')

# Thread lock for database operations
db_lock = Lock()

def get_db_connection():
    """
    Get a SQLite database connection
    Returns a connection with row_factory set to sqlite3.Row for dictionary-like access
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Initialize the database and create tables if they don't exist
    """
    conn = None
    cursor = None
    try:
        print(f"✓ Initializing database at: {DB_PATH}")
        conn = get_db_connection()
        cursor = conn.cursor()

        # Create purchase_slips table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchase_slips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT,
                company_address TEXT,
                document_type TEXT DEFAULT 'Purchase Slip',
                vehicle_no TEXT,
                date TEXT NOT NULL,
                bill_no INTEGER NOT NULL,
                party_name TEXT,
                material_name TEXT,
                ticket_no TEXT,
                broker TEXT,
                terms_of_delivery TEXT,
                sup_inv_no TEXT,
                gst_no TEXT,
                bags REAL DEFAULT 0,
                avg_bag_weight REAL DEFAULT 0,
                net_weight REAL DEFAULT 0,
                shortage_kg REAL DEFAULT 0,
                rate REAL DEFAULT 0,
                rate_basis TEXT DEFAULT '100',
                calculated_rate REAL DEFAULT 0,
                amount REAL DEFAULT 0,
                bank_commission REAL DEFAULT 0,
                postage REAL DEFAULT 0,
                batav_percent REAL DEFAULT 0,
                batav REAL DEFAULT 0,
                shortage_percent REAL DEFAULT 0,
                shortage REAL DEFAULT 0,
                dalali_rate REAL DEFAULT 0,
                dalali REAL DEFAULT 0,
                hammali_rate REAL DEFAULT 0,
                hammali REAL DEFAULT 0,
                freight REAL DEFAULT 0,
                rate_diff REAL DEFAULT 0,
                quality_diff REAL DEFAULT 0,
                quality_diff_comment TEXT,
                moisture_ded REAL DEFAULT 0,
                moisture_ded_percent REAL DEFAULT 0,
                tds REAL DEFAULT 0,
                total_deduction REAL DEFAULT 0,
                payable_amount REAL DEFAULT 0,
                payment_method TEXT,
                payment_date TEXT,
                payment_amount REAL DEFAULT 0,
                payment_bank_account TEXT,
                payment_due_date TEXT,
                payment_due_comment TEXT,
                instalment_1_date TEXT,
                instalment_1_amount REAL DEFAULT 0,
                instalment_1_comment TEXT,
                instalment_2_date TEXT,
                instalment_2_amount REAL DEFAULT 0,
                instalment_2_comment TEXT,
                instalment_3_date TEXT,
                instalment_3_amount REAL DEFAULT 0,
                instalment_3_comment TEXT,
                instalment_4_date TEXT,
                instalment_4_amount REAL DEFAULT 0,
                instalment_4_comment TEXT,
                instalment_5_date TEXT,
                instalment_5_amount REAL DEFAULT 0,
                instalment_5_comment TEXT,
                prepared_by TEXT,
                authorised_sign TEXT,
                paddy_unloading_godown TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create users table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                full_name TEXT,
                role TEXT DEFAULT 'user',
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP NULL
            )
        ''')

        # Create unloading_godowns table for dynamic dropdown
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS unloading_godowns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Check and add missing columns to purchase_slips if needed
        cursor.execute("PRAGMA table_info(purchase_slips)")
        existing_columns = {row[1] for row in cursor.fetchall()}

        columns_to_add = {
            'shortage_kg': "REAL DEFAULT 0",
            'rate_basis': "TEXT DEFAULT '100'",
            'calculated_rate': "REAL DEFAULT 0",
            'postage': "REAL DEFAULT 0",
            'payment_due_date': "TEXT",
            'payment_due_comment': "TEXT",
            'payment_bank_account': "TEXT",
            'instalment_1_date': "TEXT",
            'instalment_1_amount': "REAL DEFAULT 0",
            'instalment_1_comment': "TEXT",
            'instalment_2_date': "TEXT",
            'instalment_2_amount': "REAL DEFAULT 0",
            'instalment_2_comment': "TEXT",
            'instalment_3_date': "TEXT",
            'instalment_3_amount': "REAL DEFAULT 0",
            'instalment_3_comment': "TEXT",
            'instalment_4_date': "TEXT",
            'instalment_4_amount': "REAL DEFAULT 0",
            'instalment_4_comment': "TEXT",
            'instalment_5_date': "TEXT",
            'instalment_5_amount': "REAL DEFAULT 0",
            'instalment_5_comment': "TEXT",
            'quality_diff_comment': "TEXT",
            'moisture_ded_percent': "REAL DEFAULT 0",
            'prepared_by': "TEXT",
            'authorised_sign': "TEXT",
            'paddy_unloading_godown': "TEXT"
        }

        for col_name, col_type in columns_to_add.items():
            if col_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE purchase_slips ADD COLUMN {col_name} {col_type}")
                    print(f"✓ Added column: {col_name}")
                except sqlite3.OperationalError as e:
                    if "duplicate column" not in str(e).lower():
                        print(f"Warning: Could not add column {col_name}: {e}")

        # Create default admin user if no users exist
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]

        if user_count == 0:
            cursor.execute('''
                INSERT INTO users (username, password, full_name, role)
                VALUES ('admin', 'admin', 'Administrator', 'admin')
            ''')
            print("✓ Default admin user created (username: admin, password: admin)")

        # Add some default unloading godowns if table is empty
        cursor.execute("SELECT COUNT(*) FROM unloading_godowns")
        godown_count = cursor.fetchone()[0]

        if godown_count == 0:
            default_godowns = [
                'Godown A',
                'Godown B',
                'Main Warehouse',
                'Storage Unit 1'
            ]
            for godown in default_godowns:
                cursor.execute('INSERT OR IGNORE INTO unloading_godowns (name) VALUES (?)', (godown,))
            print(f"✓ Added {len(default_godowns)} default unloading godowns")

        conn.commit()
        print("✓ Database tables initialized successfully")

    except sqlite3.Error as err:
        print(f"❌ Error initializing database: {err}")
        if conn:
            conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_next_bill_no():
    """
    Get the next bill number
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT MAX(bill_no) as max_bill FROM purchase_slips')
        result = cursor.fetchone()

        if result[0] is None:
            return 1
        return result[0] + 1

    except sqlite3.Error as err:
        print(f"❌ Error getting next bill number: {err}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
