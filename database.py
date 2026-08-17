import sqlite3
import json
from config import DATABASE

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Channel Permissions (Sirf 3 - Send, Attach, Delete)
    c.execute('''CREATE TABLE IF NOT EXISTS channel_permissions (
        channel_id TEXT PRIMARY KEY,
        channel_name TEXT,
        can_send INTEGER DEFAULT 1,
        can_attach INTEGER DEFAULT 1,
        can_delete INTEGER DEFAULT 0
    )''')

    # Products
    c.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT,
        price TEXT,
        validity TEXT,
        features TEXT,
        image_url TEXT,
        channel_id TEXT
    )''')

    # Sent Messages Log
    c.execute('''CREATE TABLE IF NOT EXISTS sent_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message_id TEXT NOT NULL,
        channel_id TEXT NOT NULL,
        content TEXT,
        embed_json TEXT,
        file_url TEXT,
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # Templates (Sirf text templates)
    c.execute('''CREATE TABLE IF NOT EXISTS templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        content TEXT
    )''')

    conn.commit()
    conn.close()

# ------------------ Channel Permissions ------------------
def get_channel_permission(channel_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM channel_permissions WHERE channel_id = ?", (str(channel_id),))
    r = c.fetchone()
    conn.close()
    if r:
        return {"channel_id": r[0], "channel_name": r[1], "can_send": bool(r[2]), "can_attach": bool(r[3]), "can_delete": bool(r[4])}
    return None

def set_channel_permission(channel_id, channel_name, perms):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO channel_permissions 
                 (channel_id, channel_name, can_send, can_attach, can_delete)
                 VALUES (?,?,?,?,?)''',
              (str(channel_id), channel_name, perms.get('can_send',1), perms.get('can_attach',1), perms.get('can_delete',0)))
    conn.commit()
    conn.close()

def get_all_channels():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM channel_permissions")
    return [{"channel_id": r[0], "channel_name": r[1], "can_send": bool(r[2]), "can_attach": bool(r[3]), "can_delete": bool(r[4])} for r in c.fetchall()]

# ------------------ Products ------------------
def add_product(name, category, price, validity, features, image_url, channel_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("INSERT INTO products (name, category, price, validity, features, image_url, channel_id) VALUES (?,?,?,?,?,?,?)",
              (name, category, price, validity, features, image_url, channel_id))
    conn.commit()
    conn.close()

def get_products():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM products ORDER BY id DESC")
    return [{"id": r[0], "name": r[1], "category": r[2], "price": r[3], "validity": r[4], "features": r[5], "image_url": r[6], "channel_id": r[7]} for r in c.fetchall()]

def delete_product(pid):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("DELETE FROM products WHERE id = ?", (pid,))
    conn.commit()
    conn.close()

# ------------------ Sent Messages ------------------
def log_sent_message(message_id, channel_id, content, embed_json, file_url):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("INSERT INTO sent_messages (message_id, channel_id, content, embed_json, file_url) VALUES (?,?,?,?,?)",
              (str(message_id), str(channel_id), content, embed_json, file_url))
    conn.commit()
    conn.close()

def get_sent_messages(channel_id=None):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    if channel_id:
        c.execute("SELECT * FROM sent_messages WHERE channel_id = ? ORDER BY sent_at DESC LIMIT 50", (str(channel_id),))
    else:
        c.execute("SELECT * FROM sent_messages ORDER BY sent_at DESC LIMIT 50")
    return [{"id": r[0], "message_id": r[1], "channel_id": r[2], "content": r[3], "embed_json": r[4], "file_url": r[5]} for r in c.fetchall()]

def delete_sent_message_log(message_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("DELETE FROM sent_messages WHERE message_id = ?", (str(message_id),))
    conn.commit()
    conn.close()

# ------------------ Templates ------------------
def save_template(name, content):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO templates (name, content) VALUES (?,?)", (name, content))
    conn.commit()
    conn.close()

def get_templates():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT name, content FROM templates")
    return [{"name": r[0], "content": r[1]} for r in c.fetchall()]