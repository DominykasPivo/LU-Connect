import sqlite3 ##https://www.ionos.com/digitalguide/websites/web-development/sqlite3-python/  for database setup
import uuid  #https://medium.com/@nagendra.kumar1508/generating-unique-ids-using-python-a-practical-guide-97ed7729071d  for unique user id's
import hashlib #https://www.geeksforgeeks.org/md5-hash-python/ for password hashing

#database connection
with sqlite3.connect("LU-Connect.db") as connection:
    cursor = connection.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, username TEXT UNIQUE, password TEXT)")
    connection.commit()


def register_to_DB(username, password):
    user_id = str(uuid.uuid4())  
    hashed_password = hashlib.sha256(password.encode()).hexdigest()  # at first chose md5 but sha256 is more secure

    with sqlite3.connect("LU-Connect.db") as connection:
        cursor = connection.cursor()
        # Check if user already exists
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        if user:
           print("User already exists!")
           return
        cursor.execute("INSERT INTO users (id, username, password) VALUES (?, ?, ?)", (user_id, username, hashed_password))
        connection.commit()
    print("User registered successfully!")
