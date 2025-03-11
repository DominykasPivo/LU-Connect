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


def handle_request(client_socket, client_address):
    with semaphore:
        print(f"Connection from {client_address} has been established!")
        client_socket.send("Welcome to the chatroom!".encode())

        try:
            client_socket.send("Type register to create an account or login to sign in: ".encode())
            choice = client_socket.recv(1024).decode().strip().lower()
            # Register 
            if choice == "register":
                client_socket.send("Enter your username: ".encode())
                username = client_socket.recv(1024).decode()
                client_socket.send("Enter your password: ".encode())
                password = client_socket.recv(1024).decode()
                register_to_DB(username, password)
                return

            # Login
            elif choice == "login":
                client_socket.send("Enter your username: ".encode())
                username = client_socket.recv(1024).decode()
                client_socket.send("Enter your password: ".encode())
                password = client_socket.recv(1024).decode()
                user_id = login_to_DB(username, password)

                if not user_id:
                    client_socket.send("Invalid credentials!".encode())
                    return
                client_socket.send(f"Login successful! Welcome {username}!".encode())
                with clients_lock: #ensuring thread safety
                    clients[client_socket] = user_id

            #handle/broadcast the messages
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
