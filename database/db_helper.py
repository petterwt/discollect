import os
import mysql.connector
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

# Load environment variables
load_dotenv()

# THIS FILE ACTS AS THE BRIDGE BETWEEN WEB APPLICATION AND MYSQL SERVER.
# IT HAS A WAY TO CREATE A CONNECTION TO DB,
# AND THEN READ BUILT TABLES BY RUNNING schema.sql
# AND LASTLY POPULATES TABLES BY RUNNING insert.sql

def get_db_connection():
    """Establishes a fresh connection to the MySQL server."""
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "127.0.0.1"),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD"),
        database=os.environ.get("DB_NAME")
    )


DEFAULT_WEEKLY_PICK_RECORD_IDS = (1, 2, 3, 4, 5, 6)


def ensure_default_users():
    """Seed one admin and one customer account if the users table is empty."""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT COUNT(*) AS user_count FROM users")
    result = cur.fetchone() or {}
    user_count = int(result.get("user_count") or 0)

    if user_count == 0:
        cur.execute("SELECT role_id FROM roles WHERE role_name = %s", ("admin",))
        admin_role = cur.fetchone()
        cur.execute("SELECT role_id FROM roles WHERE role_name = %s", ("customer",))
        customer_role = cur.fetchone()

        if admin_role:
            cur.execute(
                "INSERT INTO users (username, password_hash, role_id) VALUES (%s, %s, %s)",
                ("admin", generate_password_hash("admin123"), admin_role["role_id"]),
            )
        if customer_role:
            cur.execute(
                "INSERT INTO users (username, password_hash, role_id) VALUES (%s, %s, %s)",
                ("customer", generate_password_hash("user123"), customer_role["role_id"]),
            )

        conn.commit()

    cur.close()
    conn.close()


def get_user_by_username(username):
    """Fetch a user by username, including their role name."""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    query = """
    SELECT users.user_id, users.username, users.password_hash, roles.role_name
    FROM users
    INNER JOIN roles ON users.role_id = roles.role_id
    WHERE users.username = %s
    LIMIT 1
    """
    cur.execute(query, (username,))
    user = cur.fetchone()

    cur.close()
    conn.close()
    return user


def get_user_records_for_table(user_id, table_name):
    """Fetch user-specific records for wishlist or collection."""
    allowed_tables = {
        "user_collection": "user_collection",
        "user_wishlist": "user_wishlist",
    }
    actual_table = allowed_tables.get(table_name)
    if not actual_table:
        raise ValueError("Invalid saved-record table")

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    query = f"""
    SELECT records.*, artists.artist_name, genres.genre_name
    FROM {actual_table}
    INNER JOIN records ON {actual_table}.record_id = records.record_id
    INNER JOIN artists ON records.artist_id = artists.artist_id
    INNER JOIN genres ON records.genre_id = genres.genre_id
    WHERE {actual_table}.user_id = %s
    ORDER BY {actual_table}.created_at DESC, records.release_date DESC
    """
    cur.execute(query, (user_id,))
    user_rows = cur.fetchall()

    cur.close()
    conn.close()

    for record in user_rows:
        if record.get('release_date'):
            record['release_year_only'] = record['release_date'].year

    return user_rows


def get_user_record_ids(user_id, table_name):
    """Return a set of record IDs already saved by the user."""
    allowed_tables = {
        "user_collection": "user_collection",
        "user_wishlist": "user_wishlist",
    }
    actual_table = allowed_tables.get(table_name)
    if not actual_table:
        raise ValueError("Invalid saved-record table")

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    query = f"SELECT record_id FROM {actual_table} WHERE user_id = %s"
    cur.execute(query, (user_id,))
    rows = cur.fetchall()

    cur.close()
    conn.close()
    return {row["record_id"] for row in rows}


def save_record_for_user(user_id, table_name, record_id):
    """Save a record in a user's collection or wishlist."""
    allowed_tables = {
        "user_collection": "user_collection",
        "user_wishlist": "user_wishlist",
    }
    actual_table = allowed_tables.get(table_name)
    if not actual_table:
        raise ValueError("Invalid saved-record table")

    conn = get_db_connection()
    cur = conn.cursor()

    query = f"INSERT IGNORE INTO {actual_table} (user_id, record_id) VALUES (%s, %s)"
    cur.execute(query, (user_id, record_id))
    inserted = cur.rowcount > 0
    conn.commit()

    cur.close()
    conn.close()
    return inserted


def remove_record_for_user(user_id, table_name, record_id):
    """Remove a record from a user's collection or wishlist."""
    allowed_tables = {
        "user_collection": "user_collection",
        "user_wishlist": "user_wishlist",
    }
    actual_table = allowed_tables.get(table_name)
    if not actual_table:
        raise ValueError("Invalid saved-record table")

    conn = get_db_connection()
    cur = conn.cursor()

    query = f"DELETE FROM {actual_table} WHERE user_id = %s AND record_id = %s"
    cur.execute(query, (user_id, record_id))
    deleted = cur.rowcount > 0
    conn.commit()

    cur.close()
    conn.close()
    return deleted


def get_admin_inventory_records():
    """Return records that are low in stock or sold out for the admin dashboard."""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    query = """
    SELECT records.*, artists.artist_name, genres.genre_name
    FROM records
    INNER JOIN artists ON records.artist_id = artists.artist_id
    INNER JOIN genres ON records.genre_id = genres.genre_id
    WHERE records.stock_qty = 0
    ORDER BY records.record_name ASC
    """
    cur.execute(query)
    records = cur.fetchall()

    cur.close()
    conn.close()

    for record in records:
        if record.get('release_date'):
            record['release_year_only'] = record['release_date'].year

    sold_out_records = [record for record in records if int(record.get('stock_qty') or 0) == 0]
    return sold_out_records


def get_catalog_records():
    """Load all catalog records with artist and genre information."""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    query = """
    SELECT records.*, artists.artist_name, genres.genre_name
    FROM records
    INNER JOIN artists ON records.artist_id = artists.artist_id
    INNER JOIN genres ON records.genre_id = genres.genre_id
    ORDER BY records.date_added DESC, records.release_date DESC
    """
    cur.execute(query)
    catalog_rows = cur.fetchall()

    cur.close()
    conn.close()

    for record in catalog_rows:
        if record.get('release_date'):
            record['release_year_only'] = record['release_date'].year

    return catalog_rows


def ensure_weekly_pick_column():
    """Ensure records.is_weekly_pick exists and has default seeded picks."""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute(
        """
        SELECT COUNT(*) AS column_count
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'records'
          AND COLUMN_NAME = 'is_weekly_pick'
        """
    )
    has_column = int((cur.fetchone() or {}).get("column_count") or 0) > 0

    if not has_column:
        cur.execute("ALTER TABLE records ADD COLUMN is_weekly_pick BOOLEAN NOT NULL DEFAULT FALSE")
        conn.commit()

    cur.execute("SELECT COUNT(*) AS pick_count FROM records WHERE is_weekly_pick = TRUE")
    pick_count = int((cur.fetchone() or {}).get("pick_count") or 0)

    if pick_count == 0 and DEFAULT_WEEKLY_PICK_RECORD_IDS:
        placeholders = ", ".join(["%s"] * len(DEFAULT_WEEKLY_PICK_RECORD_IDS))
        cur.execute(
            f"UPDATE records SET is_weekly_pick = TRUE WHERE record_id IN ({placeholders})",
            DEFAULT_WEEKLY_PICK_RECORD_IDS,
        )
        conn.commit()

    cur.close()
    conn.close()


def get_weekly_pick_records():
    """Return records flagged as weekly picks for the featured homepage grid."""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    query = """
    SELECT records.*, artists.artist_name, genres.genre_name
    FROM records
    INNER JOIN artists ON records.artist_id = artists.artist_id
    INNER JOIN genres ON records.genre_id = genres.genre_id
    WHERE records.is_weekly_pick = TRUE
    ORDER BY records.record_id ASC
    """
    cur.execute(query)
    weekly_rows = cur.fetchall()

    cur.close()
    conn.close()

    for record in weekly_rows:
        if record.get('release_date'):
            record['release_year_only'] = record['release_date'].year

    return weekly_rows


def get_homepage_metrics():
    """Return stock and new-arrival counts for the homepage cards."""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    query = """
    SELECT
        COALESCE(SUM(CASE WHEN in_stock = TRUE THEN 1 ELSE 0 END), 0) AS records_in_stock,
        COALESCE(SUM(CASE WHEN date_added >= DATE_SUB(NOW(), INTERVAL 14 DAY) THEN 1 ELSE 0 END), 0) AS new_arrivals
    FROM records
    """
    cur.execute(query)
    metrics = cur.fetchone() or {}

    cur.close()
    conn.close()

    return {
        "records_in_stock": int(metrics.get("records_in_stock") or 0),
        "new_arrivals": int(metrics.get("new_arrivals") or 0),
    }