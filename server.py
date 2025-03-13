#https://www.scaler.in/build-a-chatroom-in-python/  - this is my reference for the server.py code
import socket
import threading
import queue 
from authentication import login_to_DB, register_to_DB

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

def handle_login(client_socket, username, password):
                # Call the login_to_DB function from authentication.py
                user_id = login_to_DB(username, password)
                if user_id:
                    client_socket.send(f"Login successful! Welcome {username}!".encode())
                    return username, user_id
                else:
                    client_socket.send("Invalid credentials!".encode())
                    return None, None
                
def handle_registration(client_socket, username, password):
    # Call the register_to_DB function from authentication.py
    if register_to_DB(username, password):
        client_socket.send("Registration successful!".encode())
    else:
        client_socket.send("Registration failed!".encode())

# Function to broadcast messages to all connected clients
def broadcast_message(sender_socket, message):
    with clients_lock:
        for client in clients:
            if client != sender_socket:
                try:
                    client.send(message.encode())
                except:
                    # Remove the client if sending fails
                    del clients[client]
                    client.close()



def handle_request(client_socket, client_address):
    with semaphore:
        print(f"Connection from {client_address} has been established!")
        #client_socket.send("Welcome to the chatroom!".encode())
        try:
            # Receive the action (register or login) from the client
            action = client_socket.recv(1024).decode().strip().lower()
            if action not in ["register", "login"]:
                client_socket.send("Invalid action!".encode())
                return
            username = client_socket.recv(1024).decode().strip()
            password = client_socket.recv(1024).decode().strip()

            if action == "register":
                # Handle registration
                handle_registration(client_socket, username, password)
                return
            elif action == "login":
                # Handle login
                username, user_id = handle_login(client_socket, username, password)
                if not username:
                    return
                with clients_lock:
                    clients[client_socket] = (username, user_id)
                broadcast_message(client_socket, f"{username} has joined the chat!")
            
            while True:
                message = client_socket.recv(1024).decode()

                print(f"{client_address}: {message}")
                with clients_lock: #ensuring thread safety
                    for client in clients:
                        if client != client_socket:
                            client.send(f"{client_address}: {message}".encode())

        except Exception as e:
            print(f"Connection from {client_address} has been terminated!")
        finally:   #close the connection with all threads
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
    
    #accepting the clients
    while True:
        client_socket, client_address = server_socket.accept()
        if threading.active_count() - 1 >= 3: # take in up to three clients at once 
            print(f"[WAITING] {client_address} added to waiting queue.")
            waiting_queue.put((client_socket, client_address))
            continue
        
        threading.Thread(target=handle_request, args=(client_socket, client_address)).start()


if __name__ == "__main__":
    start_server()

#TASKS:
#implement the waiting queue
#implement the client side
#think of more implementations for the server
