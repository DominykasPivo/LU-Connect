#https://www.scaler.in/build-a-chatroom-in-python/  - this is my reference for the server.py code
import socket
import threading
import queue
from authentication import login_to_DB, register_to_DB, create_DB
import time
from datetime import datetime

# SERVER CONFIGURATION
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 7000
MAX_CLIENTS = 3  # Maximum number of active clients

clients = {}  # Dictionary to store active client sockets and usernames
clients_lock = threading.Lock()  # Lock for thread-safe access to clients dictionary

semaphore = threading.Semaphore(MAX_CLIENTS)
waiting_queue = queue.Queue()

def handle_file_transfer():
    pass


def check_queue():
    """Check if there are clients waiting in the queue and process them if space is available"""
    while not waiting_queue.empty() and threading.active_count() - 1 < MAX_CLIENTS:
        client_socket, client_address = waiting_queue.get()
        print(f"[QUEUE] Processing waiting client from {client_address}")
        threading.Thread(target=handle_request, args=(client_socket, client_address, True)).start()

def recv_all(sock):
    """Helper function to receive a complete message from the client."""
    data = b""
    while True:
        part = sock.recv(1024)
        data += part
        if b"\n" in data:
            break
    return data.decode().strip()

def handle_login(client_socket, username, password):
    """Handle login authentication"""
    print(f"Attempting to log in user: {username}")
    if login_to_DB(username, password):
        if threading.active_count() - 1 >= MAX_CLIENTS:
            position = waiting_queue.qsize() + 1
            wait_time = position * 30  # Approximate wait time in seconds
            response = f"You are in position {position} in the queue. Approximate wait time: {wait_time} seconds."
            client_socket.send(f"queue\n{response}".encode())
            print(f"User {username} placed in queue at position {position}")
            return False
        else:
            client_socket.send("success".encode())
            print(f"User {username} logged in successfully.")
            return True
    else:
        client_socket.send("Invalid credentials!".encode())
        print(f"Invalid credentials for user: {username}")
        return False

def handle_registration(client_socket, username, password):
    """Handle user registration"""
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

def broadcast_message(sender_socket, message):
    """Broadcast a message to all connected clients except the sender"""
    with clients_lock:
        for client in clients:
            if client != sender_socket:
                try:
                    username = clients[sender_socket]
                    client.send(f"{username}: {message}".encode())
                except:
                    del clients[client]
                    client.close()

def handle_request(client_socket, client_address, from_queue=False):
    """Handle client connection and requests"""
    with semaphore:
        print(f"Connection from {client_address} has been established!")
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
                    # Handle registration
                    handle_registration(client_socket, username, password)
                elif action == "login":
                    print("Login")
                    # Handle login
                    if not handle_login(client_socket, username, password):
                        client_socket.send("Invalid credentials!".encode())
                        continue
                    with clients_lock:
                        clients[client_socket] = username
                    broadcast_message(client_socket, f"{username} has joined the chat!")
                    break # exit the loop after successful login

            while True:
                message = client_socket.recv(1024).decode()
                if not message:
                    break
                print(f"{client_address}: {message}")
                broadcast_message(client_socket, f"{client_address}: {message}")

        except Exception as e:
            print(f"Connection from {client_address} has been terminated! Error: {e}")
        finally:
            with clients_lock:
                if client_socket in clients:
                    del clients[client_socket]
            client_socket.close()
            print(f"Connection from {client_address} has been closed.")

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(MAX_CLIENTS)
    print(f"Server is listening on {SERVER_HOST}:{SERVER_PORT}")

    while True:
        client_socket, client_address = server_socket.accept()
        if threading.active_count() - 1 >= MAX_CLIENTS:
            print(f"[WAITING] {client_address} added to waiting queue.")
            waiting_queue.put((client_socket, client_address))
            continue

        threading.Thread(target=handle_request, args=(client_socket, client_address)).start()

if __name__ == "__main__":
    create_DB()
    start_server()