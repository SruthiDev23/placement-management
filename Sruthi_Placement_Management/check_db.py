import mysql.connector

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="****",
    database="placement_management"
)

cur = db.cursor()

cur.execute("SELECT DATABASE()")
print("Connected Database:", cur.fetchone())

cur.execute("SHOW COLUMNS FROM users")
print("\nUSERS TABLE COLUMNS:")
for row in cur.fetchall():
    print(row)

cur.close()
db.close()