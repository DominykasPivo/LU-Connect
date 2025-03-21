import sqlite3 ##https://www.ionos.com/digitalguide/websites/web-development/sqlite3-python/  for database setup
import uuid  #https://medium.com/@nagendra.kumar1508/generating-unique-ids-using-python-a-practical-guide-97ed7729071d  for unique user id's
import hashlib #https://www.geeksforgeeks.org/md5-hash-python/ for password hashing

#database connection
def create_DB():
    with sqlite3.connect("LU-Connect.db") as connection:
        cursor = connection.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, username TEXT UNIQUE, password TEXT)")
        connection.commit()
    


def register_to_DB(username, password):
    user_id = str(uuid.uuid4())  
    hashed_password = hashlib.sha256(password.encode()).hexdigest()  # at first chose md5 but sha256 is more secure

<<<<<<< Updated upstream
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


def login_to_DB(username, password):
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    with sqlite3.connect("LU-Connect.db") as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, hashed_password))
        user = cursor.fetchone()
        if user:
            print("Login successful! User ID:", user[0])
            return user[0] # return user id and use the data for server.py
        else:
            print("Invalid credentials!")
            return None

if __name__ == "__main__":
    create_DB()
=======
        with sqlite3.connect(DB_PATH) as connection:
            cursor = connection.cursor()
            # Check if user already exists
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            if user:
                print(f"User {username} already exists!")
                return False
            # Insert the new user
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
    

>>>>>>> Stashed changes
