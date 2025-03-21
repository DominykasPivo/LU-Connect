#https://www.scaler.in/build-a-chatroom-in-python/  - this is my reference for the server.py code
import socket
import threading
import queue 
from authentication import login_to_DB, register_to_DB, create_DB
import pygame #for sound notification
import os
import time
from encryption import encrypt_message, decrypt_message

pygame.mixer.init()

#SERVER CONFIGURATION
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 7000
MAX_CLIENTS = 3 # when there will be 3 clients connected to the server, the 4th client will be added to the waiting queue. 

clients = {}
clients_lock = threading.Lock()

semaphore = threading.Semaphore(MAX_CLIENTS)
waiting_queue = queue.Queue()

sound_preferences = {}

def handle_file_transfer():
    pass

# Create directory for encrypted chat logs if it doesn't exist
if not os.path.exists("chat_logs"):
    os.makedirs("chat_logs")

def store_message(username, message):
    """Store a message in encrypted form"""
    # Create timestamp-based filename (one file per day)
    timestamp = time.strftime("%Y-%m-%d")
    filename = f"chat_logs/chat_{timestamp}.log"
    
    # Format the message with timestamp and username
    current_time = time.strftime("%H:%M:%S")
    formatted_msg = f"[{current_time}] {username}: {message}"
    
    # Encrypt the message
    encrypted_msg = encrypt_message(formatted_msg)
    
    # Append to the log file
    with open(filename, "ab") as f:  # Using binary mode for encrypted data to
        f.write(encrypted_msg + b"\n")
    
    print(f"Message encrypted and stored in {filename}")

# Function to read and decrypt chat logs for admin purposes.
# Can view past messages with read_encrypted_logs("2025-03-21") (for a specific date)
def read_encrypted_logs(date=None):
    """Utility function to read and decrypt chat logs"""
    if date is None:
        date = time.strftime("%Y-%m-%d")
    
    filename = f"chat_logs/chat_{date}.log"
    if not os.path.exists(filename):
        print(f"No chat logs found for {date}")
        return []
    
    messages = []
    with open(filename, "rb") as f:
        for line in f:
            if line.strip():
                try:
                    decrypted_msg = decrypt_message(line.strip())
                    messages.append(decrypted_msg)
                    print(decrypted_msg)
                except Exception as e:
                    print(f"[ERROR] Could not decrypt message: {e}")
    
    return messages


def recv_all(sock):
    #Helper function to receive a complete message from the client.
    data = b""
    while True:
        try:
            part = sock.recv(1024)
            if not part:
                break  # Stop if client disconnects
            data += part
            if b"\n" in data:
                break
        except ConnectionResetError:
            print("[WARNING] Client forcibly closed connection.")
            return None  # Return None if connection was lost
    return data.decode().strip() if data else None


def handle_login(client_socket, username, password):
    print(f"Attempting to log in user: {username}")
    try:
        if login_to_DB(username, password):
            response = "success"
            client_socket.send(response.encode())
            print(f"User {username} logged in successfully.")
            return True
        else:
            client_socket.send("Invalid credentials!".encode())
            print(f"Invalid credentials for user: {username}")
            return False
    except Exception as e:
        response = f"Error during login: {e}"
        client_socket.send(response.encode())       
        print(response)
        return False 
    
    
                
def handle_registration(client_socket, username, password):
    # Call the register_to_DB function from authentication.py
    print(f"Attempting to register user: {username}")
    try:
        if register_to_DB(username, password):
            response = "success"
            client_socket.send(response.encode())
            print(f"User {username} registered successfully.")
        else:
            response = "User already exists!"
            client_socket.send(response.encode())
            print(f"User {username} already exists.")
    except Exception as e:
        response = f"Error during registration: {e}"
        client_socket.send(response.encode())
        print(response)

# Function to broadcast messages to all connected clients
def broadcast_message(sender_socket, message):
    with clients_lock:
        sender_username = clients.get(sender_socket, "Unknown")
        for client in clients:
            if client != sender_socket:
                try:
                    client.send(f"{sender_username}: {message}".encode())
                    if sound_preferences.get(client, False):
                        pygame.mixer.music.load('notification.mp3')
                        pygame.mixer.music.play()
                except:
                    # Remove the client if sending fails
                    del clients[client]
                    client.close()



def handle_request(client_socket, client_address):
    with clients_lock:
        if len(clients) >= MAX_CLIENTS:  # If server is full
            print(f"[WAITING] {client_address} added to queue.")
            waiting_queue.put((client_socket, client_address))
            client_socket.send("queue".encode())  # Notify client they're in queue
            return  # Exit this function so they don't proceed to chat immediately
    with semaphore:
        print(f"semaphore value: ", semaphore._value)
        print(f"Connection from {client_address} has been established!")
        #client_socket.send("Welcome to the chatroom!".encode())
        try:
            while True:  # Loop to handle registration and login requests
            # Receive the action (register or login) from the client
                data = recv_all(client_socket)
                print(f"Received data: {data}")

                parts = data.split("\n")
                if len(parts) < 3:
                    client_socket.send("Invalid request!".encode())
                    return
            
                action = parts[0].strip()
                username = parts[1].strip()
                password = parts[2].strip()

                print(f"Action: {action}, Username: {username}, Password: {password}")  # Debug stat


                if action == "register":
                    handle_registration(client_socket, username, password)
                elif action == "login":
                    if handle_login(client_socket, username, password):
                        with clients_lock:
                            clients[client_socket] = username
                            sound_preferences[client_socket] = False  # Default to sound off
                        broadcast_message(client_socket, "has joined the chat!")
                        break  # Exit the loop after successful login
                    else:
                        client_socket.send("Invalid credentials!".encode())
                else:
                    client_socket.send("Invalid action!".encode())
            # Handle chat messages
            while True:
                message = client_socket.recv(1024).decode()
                if not message:  # Client disconnected
                    break
                print(f"{client_address}: {message}")
                if "toggle_sound" in message:
                    with clients_lock:
                        sound_preferences[client_socket] = not sound_preferences.get(client_socket, False)
                        status = "enabled" if sound_preferences[client_socket] else "disabled"
                        client_socket.send(f"Sound {status}".encode())
                        print(f"Sound {status} for {clients[client_socket]}")
                else:
                    # Store the message in encrypted form
                    with clients_lock:
                        current_username = clients[client_socket]
                    store_message(current_username, message)
                    with clients_lock: #ensuring thread safety
                        for client in clients:
                            if client != client_socket:
                                try:
                                    client.send(f"{username}: {message}".encode())
                                    if sound_preferences.get(client, False):
                                        pygame.mixer.music.load('notification.mp3')
                                        pygame.mixer.music.play()
                                except:
                                    # Remove the client if sending fails
                                    del clients[client]
                                    client.close()

        except Exception as e:
            print(f"Connection from {client_address} has been terminated!")
        finally:   #close the connection with all threads
            print(f"[DEBUG] Finally block executing for {client_address}")
            with clients_lock:
                if client_socket in clients:
                    username = clients[client_socket]
                    del clients[client_socket]
                    del sound_preferences[client_socket]
            print(f"Connection from {client_address} has been closed.")
            client_socket.close()
            semaphore.release()
            print("semaphore value: ", semaphore._value)
            print("cehcking queue")
            if not waiting_queue.empty():
                queue_client_socket, queue_client_address = waiting_queue.get()
                print(f"[QUEUE] Moving {client_address} from queue to active clients.")
                queue_client_socket.send("welcome".encode())  # Notify client they can join
                threading.Thread(target=handle_request, args=(queue_client_socket, queue_client_address)).start()

        

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(MAX_CLIENTS)
    print(f"Server is listening on {SERVER_HOST}:{SERVER_PORT}")

    # Can view past messages with read_encrypted_logs("2025-03-21") (for a specific date)
    #read_encrypted_logs("2025-03-21")


    #accepting the clients
    while True:
        client_socket, client_address = server_socket.accept()
        with clients_lock:
            active_clients = len(clients)
        if active_clients >= MAX_CLIENTS: # take in up to three clients at once 
            print(f"[WAITING] {client_address} added to waiting queue.")
            waiting_queue.put((client_socket, client_address))
            client_socket.send("queue".encode())
        else:
            client_socket.send("no queue".encode())
            threading.Thread(target=handle_request, args=(client_socket, client_address)).start()


if __name__ == "__main__":
    create_DB()
    start_server()
