import sqlite3

DATABASE = "civicai.db"


def create_database():

    connection = sqlite3.connect(DATABASE)

    cursor = connection.cursor()


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            email TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL,

            role TEXT NOT NULL

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

            image_path TEXT

        )
    """)


    connection.commit()

    connection.close()


if __name__ == "__main__":

    create_database()

    print("CivicAI database created successfully!")