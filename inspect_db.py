import sqlite3

conn = sqlite3.connect("localhub.db")
cur = conn.cursor()

cur.execute("SELECT title FROM locations;")
rows = cur.fetchall()

print("Locations:")
for row in rows:
    print("-", row[0])

conn.close()