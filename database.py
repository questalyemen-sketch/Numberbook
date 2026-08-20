import sqlite3
from config import DB_NAME


# ==========================================
# الاتصال بقاعدة البيانات
# ==========================================

def get_connection():
    return sqlite3.connect(DB_NAME)


# ==========================================
# إنشاء الجداول
# ==========================================

def init_database():

    conn = get_connection()
    cursor = conn.cursor()

    # جدول الأرقام
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS numbers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT UNIQUE NOT NULL,
            name TEXT,
            country TEXT,
            owner_user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # جدول عمليات البحث
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # جدول المستخدمين
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            first_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# ==========================================
# إضافة مستخدم
# ==========================================

def add_user(telegram_id, username, first_name):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO users
        (telegram_id, username, first_name)
        VALUES (?, ?, ?)
    """, (
        telegram_id,
        username,
        first_name
    ))

    conn.commit()
    conn.close()


# ==========================================
# إضافة رقم
# ==========================================

def add_number(phone, name, country, owner_user_id):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            INSERT INTO numbers
            (phone, name, country, owner_user_id)
            VALUES (?, ?, ?, ?)
        """, (
            phone,
            name,
            country,
            owner_user_id
        ))

        conn.commit()

        result = True

    except sqlite3.IntegrityError:

        result = False

    conn.close()

    return result


# ==========================================
# البحث عن رقم
# ==========================================

def find_number(phone):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            phone,
            name,
            country,
            owner_user_id,
            created_at
        FROM numbers
        WHERE phone = ?
    """, (phone,))

    result = cursor.fetchone()

    conn.close()

    return result


# ==========================================
# تسجيل عملية بحث
# ==========================================

def add_search(user_id, phone):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO searches
        (user_id, phone)
        VALUES (?, ?)
    """, (
        user_id,
        phone
    ))

    conn.commit()
    conn.close()


# ==========================================
# عدد الأرقام
# ==========================================

def count_numbers():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM numbers
    """)

    result = cursor.fetchone()[0]

    conn.close()

    return result


# ==========================================
# عدد عمليات البحث
# ==========================================

def count_searches():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM searches
    """)

    result = cursor.fetchone()[0]

    conn.close()

    return result


# ==========================================
# عدد المستخدمين
# ==========================================

def count_users():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM users
    """)

    result = cursor.fetchone()[0]

    conn.close()

    return result


# ==========================================
# حذف رقم
# ==========================================

def delete_number(phone, owner_user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM numbers
        WHERE phone = ?
        AND owner_user_id = ?
    """, (
        phone,
        owner_user_id
    ))

    deleted = cursor.rowcount > 0

    conn.commit()
    conn.close()

    return deleted


# ==========================================
# تشغيل إنشاء قاعدة البيانات
# ==========================================

if __name__ == "__main__":
    init_database()
    print("✅ Database initialized successfully.")