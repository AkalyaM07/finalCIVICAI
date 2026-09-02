import sqlite3

connection = sqlite3.connect("civicai.db")

cursor = connection.cursor()

cursor.execute("SELECT * FROM complaints")

rows = cursor.fetchall()

for row in rows:
    print(row)

connection.close()