#https://www.scaler.in/build-a-chatroom-in-python/  - this is my reference for the server.py code
import socket
import threading
import queue 
from authentication import login_to_DB, register_to_DB, create_DB
import time
#SERVER CONFIGURATION
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 7000
MAX_CLIENTS = 10 # when there will be 3 clients connected to the server, the 4th client will be added to the waiting queue. 

clients = {}
clients_lock = threading.Lock()

semaphore = threading.Semaphore(MAX_CLIENTS)
waiting_queue = queue.Queue()

def handle_file_transfer():
    pass


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
    print(f"Attempting to log in user: {username}")
    if login_to_DB(username, password):
        client_socket.send("Login successful!".encode())
        print(f"User {username} logged in successfully.")
        return True  # Return True for successful login
    else:
        client_socket.send("Invalid credentials!".encode())
        print(f"Invalid credentials for user: {username}")
        return False  # Return False for failed login
                
def handle_registration(client_socket, username, password):
    # Call the register_to_DB function from authentication.py
    print(f"Attempting to register user: {username}")
    if register_to_DB(username, password):
        client_socket.send("Registration successful!".encode())
        print(f"User {username} registered successfully.")
    else:
        client_socket.send("User already exists!".encode())
        print(f"User {username} already exists.")

# Function to broadcast messages to all connected clients
def broadcast_message(sender_socket, message):
    with clients_lock:
        for client in clients:
            if client != sender_socket:
                try:
                    username = clients[sender_socket]  # Get the sender's username
                    client.send(f"{username}: {message}".encode())
                except:
                    # Remove the client if sending fails
                    del clients[client]
                    client.close()



def handle_request(client_socket, client_address):
    with semaphore:
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
                    # Handle registration
                    handle_registration(client_socket, username, password)
                elif action == "login":
                    print("Login")
                    # Handle login
                    if not handle_login(client_socket, username, password):
                        continue
                    with clients_lock:
                        clients[client_socket] = username
                    broadcast_message(client_socket, f"{username} has joined the chat!")
                    break # exit the loop after successful login
            
            while True:
                message = client_socket.recv(1024).decode()
                if not message:  # Client disconnected
                    break
                print(f"{client_address}: {message}")
                with clients_lock: #ensuring thread safety
                    for client in clients:
                        if client != client_socket:
                            try:
                                client.send(f"{username}: {message}".encode())
                            except:
                                # Remove the client if sending fails
                                del clients[client]
                                client.close()

        except Exception as e:
            print(f"Connection from {client_address} has been terminated!")
        finally:   #close the connection with all threads
            with clients_lock:
                if client_socket in clients:
                    del clients[client_socket]
            client_socket.close()
            print(f"Connection from {client_address} has been closed.")

            if not waiting_queue.empty():
                client_socket, client_address = waiting_queue.get()
                threading.Thread(target=handle_request, args=(client_socket, client_address)).start()
        

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(MAX_CLIENTS)
    print(f"Server is listening on {SERVER_HOST}:{SERVER_PORT}")
    
    #accepting the clients
    while True:
        client_socket, client_address = server_socket.accept()
        if threading.active_count() - 1 >= 3: # take in up to three clients at once 
            print(f"[WAITING] {client_address} added to waiting queue.")
            waiting_queue.put((client_socket, client_address))
            continue
        
        threading.Thread(target=handle_request, args=(client_socket, client_address)).start()


if __name__ == "__main__":
    create_DB()
    start_server()

#TASKS:
#implement the waiting queue
#implement the client side
#think of more implementations for the server
