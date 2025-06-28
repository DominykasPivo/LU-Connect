#https://www.scaler.in/build-a-chatroom-in-python/  - this is my reference for the server.py code
import socket
import threading
import queue 
from authentication import login_to_DB, register_to_DB, create_DB
import pygame
import os
import time
from encryption import encrypt_message, decrypt_message

# Server configuration constants
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 7000
MAX_CLIENTS = 3
WAIT_TIME_PER_POSITION = 2  # 2 minutes per position in the waiting queue

# Initialize pygame for sound notifications
pygame.mixer.init()

class ServerManager:
    """Singleton class to manage server resources
    This class follows the Singleton design pattern to ensure only one instance
    manages all server-wide resources like client connections, semaphores,
    and the waiting queue system.
    """
    _instance = None # Class-level variable to store the singleton instance
    
    def __new__(cls):
        # Implementation of Singleton pattern:
        # Only create a new instance if none exists
        if cls._instance is None:
            cls._instance = super(ServerManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize server resources"""
        self.clients = {}
        self.clients_lock = threading.Lock()
        self.semaphore = threading.Semaphore(MAX_CLIENTS)
        self.sound_preferences = {}
        self.waiting_queue = queue.Queue()
    
    def add_client(self, client_socket, username):
        """Add a client to the active clients list"""
        with self.clients_lock:
            self.clients[client_socket] = username
            self.sound_preferences[client_socket] = False
    
    def remove_client(self, client_socket):
        """Remove a client from the active clients list and return their username"""
        username = None
        with self.clients_lock:
            if client_socket in self.clients:
                username = self.clients[client_socket]
                del self.clients[client_socket]
            
            if client_socket in self.sound_preferences:
                del self.sound_preferences[client_socket]
        
        return username
    
    def toggle_sound(self, client_socket):
        """Toggle sound preferences for a client"""
        with self.clients_lock:
            self.sound_preferences[client_socket] = not self.sound_preferences.get(client_socket, False)
            return self.sound_preferences[client_socket]
    
    def broadcast_message(self, sender_socket, message):
        """Broadcast a message to all clients except the sender"""
        with self.clients_lock:
            sender_username = self.clients.get(sender_socket, "Unknown")
            for client in list(self.clients.keys()):
                if client != sender_socket:
                    try:
                        client.send(f"{sender_username}: {message}".encode())
                        if self.sound_preferences.get(client, False):
                            pygame.mixer.music.load('notification.mp3')
                            pygame.mixer.music.play()
                    except Exception as e:
                        print(f"Error sending to {self.clients.get(client, 'unknown')}: {e}")
                        try:
                            del self.clients[client]
                            if client in self.sound_preferences:
                                del self.sound_preferences[client]
                            client.close()
                        except:
                            pass
    
    def update_waiting_clients(self):
        """Send updated queue position and wait time to all waiting clients"""
        position = 1
        with self.clients_lock:
            for client_info in list(self.waiting_queue.queue):
                client_socket, _ = client_info
                try:
                    wait_minutes = position * WAIT_TIME_PER_POSITION
                    update_msg = f"queue_update:{position}:{wait_minutes}"
                    client_socket.send(update_msg.encode())
                    position += 1
                except:
                    # If send fails, client is gone - we'll clean it up later
                    pass
    
    def add_to_waiting_queue(self, client_socket, client_address):
        """Add a client to the waiting queue"""
        with self.clients_lock:
            self.waiting_queue.put((client_socket, client_address))
    
    def get_next_from_queue(self):
        """Get the next client from the waiting queue"""
        with self.clients_lock:
            if not self.waiting_queue.empty():
                return self.waiting_queue.get()
            return None, None
    
    def queue_is_empty(self):
        """Check if the waiting queue is empty"""
        with self.clients_lock:
            return self.waiting_queue.empty()


class ChatLogger:
    """Singleton class to manage chat logging"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ChatLogger, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize logger"""
        if not os.path.exists("chat_logs"):
            os.makedirs("chat_logs")
    
    def store_message(self, username, message):
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
        with open(filename, "ab") as f:
            f.write(encrypted_msg + b"\n")
        
        print(f"Message encrypted and stored in {filename}")
    
    def read_logs(self, date=None):
        """Read and decrypt logs for a specific date"""
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


class AuthenticationManager:
    """Singleton class to manage user authentication"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AuthenticationManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize authentication resources"""
        create_DB()
    
    def login(self, username, password):
        """Authenticate a user"""
        return login_to_DB(username, password)
    
    def register(self, username, password):
        """Register a new user"""
        return register_to_DB(username, password)


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


def handle_request(client_socket, client_address):
    """Handle a client connection, including authentication and message processing"""
    print(f"Connection from {client_address} has been established!")
    
    # Get singleton instances
    server_mgr = ServerManager()
    auth_mgr = AuthenticationManager()
    chat_logger = ChatLogger()
    
    try:
        # Authentication phase
        while True:
            data = recv_all(client_socket)
            print(f"Received data: {data}")
            
            if not data:
                print(f"Client {client_address} disconnected during authentication")
                return
                
            parts = data.split("\n")
            if len(parts) < 3:
                client_socket.send("Invalid request!".encode())
                continue
            
            action = parts[0].strip()
            username = parts[1].strip()
            password = parts[2].strip()
            
            print(f"Action: {action}, Username: {username}, Password: {password}")
            
            if action == "register":
                if auth_mgr.register(username, password):
                    client_socket.send("success".encode())
                    print(f"User {username} registered successfully.")
                else:
                    client_socket.send("User already exists!".encode())
                    print(f"User {username} already exists.")
            elif action == "login":
                if auth_mgr.login(username, password):
                    client_socket.send("success".encode())
                    print(f"User {username} logged in successfully.")
                    server_mgr.add_client(client_socket, username)
                    server_mgr.broadcast_message(client_socket, "has joined the chat!")
                    break  # Exit authentication loop after successful login
                else:
                    client_socket.send("Invalid credentials!".encode())
                    print(f"Invalid credentials for user: {username}")
            else:
                client_socket.send("Invalid action!".encode())
        
        # Message handling phase - only reached after successful login
        while True:
            message = client_socket.recv(1024).decode()
            if not message:  # Client disconnected
                break
                
            print(f"{client_address}: {message}")
            
            if "toggle_sound" in message:
                sound_enabled = server_mgr.toggle_sound(client_socket)
                status = "enabled" if sound_enabled else "disabled"
                client_socket.send(f"Sound {status}".encode())
                print(f"Sound {status} for {server_mgr.clients[client_socket]}")
            else:
                # Store the message in encrypted form
                current_username = server_mgr.clients[client_socket]
                chat_logger.store_message(current_username, message)
                
                # Broadcast to other clients
                server_mgr.broadcast_message(client_socket, message)
                                    
    except Exception as e:
        print(f"Error handling client {client_address}: {e}")
    finally:
        # Clean up resources
        print(f"[DEBUG] Finally block executing for {client_address}")
        
        client_username = server_mgr.remove_client(client_socket)
        
        if client_username:
            server_mgr.broadcast_message(None, f"{client_username} has left the chat")
        
        try:
            client_socket.close()
        except:
            pass
            
        # Release semaphore and check waiting queue
        server_mgr.semaphore.release()
        print(f"Semaphore value: {server_mgr.semaphore._value}")
        
        queue_client_socket, queue_client_address = server_mgr.get_next_from_queue()
        if queue_client_socket:
            print(f"[QUEUE] Moving {queue_client_address} from queue to active clients.")
            queue_client_socket.send("welcome".encode())
            threading.Thread(target=handle_request, args=(queue_client_socket, queue_client_address)).start()
            server_mgr.update_waiting_clients()


def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(MAX_CLIENTS)
    print(f"Server is listening on {SERVER_HOST}:{SERVER_PORT}")
    
    server_mgr = ServerManager()
    
    # Start a thread to update waiting clients every 30 seconds
    def queue_updater():
        while True:
            time.sleep(30)  
            if not server_mgr.queue_is_empty():
                server_mgr.update_waiting_clients()
    
    threading.Thread(target=queue_updater, daemon=True).start()
    
    # Accepting clients
    while True:
        client_socket, client_address = server_socket.accept()
        if server_mgr.semaphore.acquire(blocking=False):
            client_socket.send("no queue".encode())
            threading.Thread(target=handle_request, args=(client_socket, client_address)).start()
        else:
            print(f"[WAITING] {client_address} added to waiting queue.")
            server_mgr.add_to_waiting_queue(client_socket, client_address)
            client_socket.send("queue".encode())


if __name__ == "__main__":
    # Create or ensure the database exists
    AuthenticationManager()  # This will call _initialize which creates the DB
    print("Starting the server...")
    start_server()
