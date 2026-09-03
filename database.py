import sqlite3


DATABASE = "civicai.db"


def create_database():

    connection = sqlite3.connect(DATABASE)

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL
                CHECK(length(trim(name)) >= 2),

            email TEXT NOT NULL UNIQUE
                CHECK(
                    email GLOB '*@*.*'
                    AND email NOT GLOB '* *'
                ),

            password TEXT NOT NULL
                CHECK(
                    length(password) >= 8
                    AND password GLOB '*[A-Z]*'
                    AND password GLOB '*[a-z]*'
                    AND password GLOB '*[0-9]*'
                    AND password GLOB '*[^A-Za-z0-9]*'
                ),

            phone TEXT NOT NULL
                CHECK(
                    length(phone) = 10
                    AND phone GLOB '[0-9]*'
                    AND phone NOT GLOB '*[^0-9]*'
                ),

            role TEXT NOT NULL
                CHECK(role IN ('user', 'admin'))

        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaints (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            complaint_id TEXT UNIQUE,

            citizen_name TEXT,

            phone TEXT,

            description TEXT,

            category TEXT,

            priority TEXT,

            department TEXT,

            location TEXT,

            status TEXT,

            source TEXT,

            created_at TEXT,

            sla_deadline TEXT,

            ai_confidence REAL,

            image_path TEXT,

            escalation_status TEXT DEFAULT 'Not Escalated',

            escalated_to TEXT,

            escalated_at TEXT

        )
    """)

    columns = cursor.execute(
        "PRAGMA table_info(complaints)"
    ).fetchall()

    column_names = [column[1] for column in columns]

    if "escalation_status" not in column_names:
        cursor.execute("""
            ALTER TABLE complaints
            ADD COLUMN escalation_status TEXT
            DEFAULT 'Not Escalated'
        """)

    if "escalated_to" not in column_names:
        cursor.execute("""
            ALTER TABLE complaints
            ADD COLUMN escalated_to TEXT
        """)

    if "escalated_at" not in column_names:
        cursor.execute("""
            ALTER TABLE complaints
            ADD COLUMN escalated_at TEXT
        """)

    connection.commit()

    connection.close()


if __name__ == "__main__":

    create_database()

    print("CivicAI database created successfully!")