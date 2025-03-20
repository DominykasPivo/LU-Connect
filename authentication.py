import sqlite3 ##https://www.ionos.com/digitalguide/websites/web-development/sqlite3-python/  for database setup
import uuid  #https://medium.com/@nagendra.kumar1508/generating-unique-ids-using-python-a-practical-guide-97ed7729071d  for unique user id's
import hashlib #https://www.geeksforgeeks.org/md5-hash-python/ for password hashing
import os  #https://www.geeksforgeeks.org/python-os-path-join-method/ for database connection

DB_PATH = os.path.join(os.path.dirname(__file__), "LU-Connect.db")
#database connection
def create_DB():
    try:
        with sqlite3.connect(DB_PATH) as connection:
            cursor = connection.cursor()
            # Important: Make sure password is NOT marked as UNIQUE
            cursor.execute("CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, username TEXT UNIQUE, password TEXT UNIQUE)")
            connection.commit()
            print(f"Successfully connected to database at {DB_PATH}")
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    except Exception as e:
        print(f"Error creating/connecting to database: {e}")

def register_to_DB(username, password):
    try:
        user_id = str(uuid.uuid4())
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        with sqlite3.connect(DB_PATH) as connection:
            cursor = connection.cursor()
            # Check if user already exists
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            if user:
                print(f"User {username} already exists!")
                return False

            # Insert the new user
            print(f"Inserting new user {username} with ID {user_id}")
            cursor.execute("INSERT INTO users (id, username, password) VALUES (?, ?, ?)", 
                          (user_id, username, hashed_password))
            # Don't forget to commit the transaction
            connection.commit()
            print(f"User {username} registered successfully!")
            return True
    except sqlite3.Error as e:
        print(f"SQLite error during registration: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error during registration: {e}")
        return False


def login_to_DB(username, password):
    try:
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        with sqlite3.connect(DB_PATH) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            if user and user[0] == hashed_password:
                print(f"User {username} logged in successfully.")
                return True
            else:
                print(f"Invalid credentials for user: {username}")
                return False
    except sqlite3.Error as e:
        print(f"SQLite error during login: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error during login: {e}")
        return False