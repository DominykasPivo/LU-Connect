#https://www.scaler.in/build-a-chatroom-in-python/  - this is my reference for the server.py code
import socket
import threading
import queue 
from authentication import login_to_DB, register_to_DB, create_DB
import time
import pygame

pygame.mixer.init()

#SERVER CONFIGURATION
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 7000
MAX_CLIENTS = 3 # when there will be 3 clients connected to the server, the 4th client will be added to the waiting queue. 

clients = {}
clients_lock = threading.Lock()

semaphore = threading.Semaphore(2)
waiting_queue = queue.Queue()

sound_preferences = {}

def handle_file_transfer():
    pass


def recv_all(sock):
    """Helper function to receive a complete message from the client."""
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
            client_socket.send("success".encode())
            print(f"User {username} logged in successfully.")
            return False
    except Exception as e:
        response = f"Error during login: {e}"
        client_socket.send(response.encode())        
    
    
                
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
        if len(clients) >= 2:  # If server is full
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

        
# def manage_waiting_queue():
#     with clients_lock:
#             active_clients = len(clients)

#     while True:
#         if not waiting_queue.empty() and  active_clients < 2:
#             client_socket, client_address = waiting_queue.get()
#             print(f"[QUEUE] Moving {client_address} from queue to active clients.")
#             client_socket.send("welcome".encode())  # Notify client they can join
#             threading.Thread(target=handle_request, args=(client_socket, client_address)).start()
#         time.sleep(1)



def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(2)
    print(f"Server is listening on {SERVER_HOST}:{SERVER_PORT}")
    
    #threading.Thread(target=manage_waiting_queue, daemon=True).start()

    #accepting the clients
    while True:
        client_socket, client_address = server_socket.accept()
        with clients_lock:
            active_clients = len(clients)
        if active_clients >= 2: # take in up to three clients at once 
            print(f"[WAITING] {client_address} added to waiting queue.")
            waiting_queue.put((client_socket, client_address))
            client_socket.send("queue".encode())
        else:
            client_socket.send("no queue".encode())
            threading.Thread(target=handle_request, args=(client_socket, client_address)).start()


if __name__ == "__main__":
    create_DB()
    start_server()

#TASKS:
#implement the waiting queue
#implement the client side
#think of more implementations for the server