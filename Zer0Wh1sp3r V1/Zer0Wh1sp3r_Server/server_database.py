import sqlite3
from pathlib import Path


# This gets the folder where this database file is located.
BASE_DIR = Path(__file__).resolve().parent

# This creates/uses a "server" folder next to server.py/server_database.py.
DB_DIR = BASE_DIR / "server"

# This is the actual SQLite database file.
DB_PATH = DB_DIR / "zer0wh1sp3r.db"


def get_connection():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    DB_DIR.mkdir(parents=True, exist_ok=True)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            receiver TEXT NOT NULL,
            encrypted_key BLOB NOT NULL,
            iv BLOB NOT NULL,
            ciphertext BLOB NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def save_message(sender, receiver, encrypted_key, iv, ciphertext, created_at):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO messages (
            sender,
            receiver,
            encrypted_key,
            iv,
            ciphertext,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        sender,
        receiver,
        encrypted_key,
        iv,
        ciphertext,
        created_at
    ))

    conn.commit()

    message_id = cursor.lastrowid

    conn.close()

    return message_id


def get_messages_for_receiver(receiver):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, sender, receiver, created_at
        FROM messages
        WHERE LOWER(receiver) = LOWER(?)
        ORDER BY id ASC
    """, (receiver,))

    rows = cursor.fetchall()

    conn.close()

    messages = []

    for row in rows:
        messages.append({
            "id": row[0],
            "sender": row[1],
            "receiver": row[2],
            "created_at": row[3]
        })

    return messages


def get_message_by_id(message_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, sender, receiver, encrypted_key, iv, ciphertext, created_at
        FROM messages
        WHERE id = ?
    """, (message_id,))

    row = cursor.fetchone()

    conn.close()

    if row is None:
        return None

    return {
        "id": row[0],
        "sender": row[1],
        "receiver": row[2],
        "encrypted_key": row[3],
        "iv": row[4],
        "ciphertext": row[5],
        "created_at": row[6]
    }


def get_latest_message_for_receiver(receiver):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, sender, receiver, encrypted_key, iv, ciphertext, created_at
        FROM messages
        WHERE LOWER(receiver) = LOWER(?)
        ORDER BY id DESC
        LIMIT 1
    """, (receiver,))

    row = cursor.fetchone()

    conn.close()

    if row is None:
        return None

    return {
        "id": row[0],
        "sender": row[1],
        "receiver": row[2],
        "encrypted_key": row[3],
        "iv": row[4],
        "ciphertext": row[5],
        "created_at": row[6]
    }


def get_total_message_count():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM messages
    """)

    count = cursor.fetchone()[0]

    conn.close()

    return count