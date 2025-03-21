import socket
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext
from tkinter import messagebox, scrolledtext, ttk
from datetime import datetime
#https://www.geeksforgeeks.org/python-gui-tkinter/
#https://www.geeksforgeeks.org/gui-chat-application-using-tkinter-in-python/
#https://docs.python.org/3/library/tkinter.html

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 7000
FORMAT = "utf-8"

class GUI:
    def __init__(self, root):
        """Connect to the server"""
        self.root = root
        self.root.geometry("250x250")
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        try:
            self.client_socket.connect((SERVER_HOST, SERVER_PORT))
            response = self.client_socket.recv(1024).decode(FORMAT)
            """Check if the server is full"""
            if response == "queue":
                self.waiting_window()
            else:
                self.login_or_register()
        except Exception as e:
            print(f"Error connecting to server: {e}")
            messagebox.showerror("Error", f"Error connecting to server: {e}")
            return
        
    #  Handling window close event
    def on_closing(self):
        try:
            self.client_socket.close()  # Close the socket connection
            print("Socket connection closed")
        except Exception as e:
            print(f"Error closing socket: {e}")
        self.root.destroy()  # Destroy the window

    def login_or_register(self):
        """Display the login or register window"""
        self.root.title("Login/Register")
        for widget in self.root.winfo_children():
            widget.destroy()
        tk.Label(self.root, text="Do you want to login or register?").pack()
        tk.Button(self.root, text="Login", command=self.login_window).pack()
        tk.Button(self.root, text="Register", command=self.register_window).pack()


    def login_window(self):
        """Display the login window"""
        self.root.title("Login")
        for widget in self.root.winfo_children():
            widget.destroy()

        tk.Label(self.root, text="Username").pack()
        username_entry = tk.Entry(self.root)
        username_entry.pack()

        tk.Label(self.root, text="Password").pack()
        password_entry = tk.Entry(self.root, show="*")
        password_entry.pack()

        def login():
            self.username = username_entry.get()
            self.password = password_entry.get()
            try:
                message = f"login\n{self.username}\n{self.password}\n"
                print(message)
                self.client_socket.sendall(message.encode(FORMAT))

                # Wait for the server's response
                response = self.client_socket.recv(1024).decode(FORMAT)
                if "success" in response.lower():
                    messagebox.showinfo("Success", "Login successful!")
                    self.chat_window()  # Open the chat window
                # elif "queue" in response.lower():
                #     messagebox.showinfo("Queue", "Server is full. You are in a waiting queue.")
                #     self.waiting_window()  # Open the waiting window
                else:
                    messagebox.showerror("Error", "Invalid credentials!")
            except Exception as e:
                print(f"Error during login: {e}")
                messagebox.showerror("Error", f"Error during login: {e}")
        tk.Button(self.root, text="Login", command=login).pack()
        tk.Button(self.root, text="Go back", command=self.login_or_register).pack()

    def register_window(self):
        """Display the register window"""
        self.root.title("Register")
        for widget in self.root.winfo_children():
            widget.destroy()

        tk.Label(self.root, text="Username").pack()
        username_entry = tk.Entry(self.root)
        username_entry.pack()

        tk.Label(self.root, text="Password").pack()
        password_entry = tk.Entry(self.root, show="*")
        password_entry.pack()
        
        def register():
            try:
                self.username = username_entry.get()
                self.password = password_entry.get()

                print(f"Sending registration request for user username: {self.username}")
                print(f"Sending registration request for user password: {self.password}")

                message = f"register\n{self.username}\n{self.password}\n"
                self.client_socket.sendall(message.encode(FORMAT))

                # Wait for the server's response
                response = self.client_socket.recv(1024).decode(FORMAT)
                print(f"Registration response: {response}")
                if "success" in response.lower():
                    messagebox.showinfo("Success", "Registration successful!")

                     # Close the current socket and create a new one for login
                    # self.client_socket.close()
                    # self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    # self.client_socket.connect((SERVER_HOST, SERVER_PORT))

                    self.login_window()  # Open the login window

                else:
                    messagebox.showerror("Error", "Invalid credentials!")
            except Exception as e:
                print(f"Error during registration: {e}")
                messagebox.showerror("Error", f"Error during registration: {e}")
        tk.Button(self.root, text="Register", command=register).pack()
        tk.Button(self.root, text="Go back", command=self.login_or_register).pack()

    def waiting_window(self):
        """Display the waiting window (queue)"""
        self.root.title("Waiting Room")
        for widget in self.root.winfo_children():
            widget.destroy()
        tk.Label(self.root, text="You are in the queue. Please wait...").pack()
        self.wait_label = tk.Label(self.root, text="Checking status...")
        self.wait_label.pack()
        # Main waiting label
        waiting_label = tk.Label(self.root, text="You are in the waiting queue",font=("Arial", 14, "bold"))
        waiting_label.pack(pady=10)

        # Position info
        self.position_label = tk.Label(self.root,text="Retrieving your position...",font=("Arial", 12))
        self.position_label.pack(pady=5)

        self.wait_time_label = tk.Label(self.root, text="Estimating wait time...", font=("Arial", 12))
        self.wait_time_label.pack(pady=5)

        # Progress bar
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=200, mode="indeterminate")
        self.progress.pack(pady=20)
        self.progress.start()
        # Status message
        self.status_label = tk.Label(self.root, text="Please wait while we find a slot for you.",font=("Arial", 10),fg="blue")
        self.status_label.pack(pady=10)

        def check_status():
            try:
                while True:
                    response = self.client_socket.recv(1024).decode(FORMAT)
                    if "welcome" in response.lower():
                        messagebox.showinfo("Access Granted", "You can use the chat!")
                        self.login_or_register()
                        break
                    # Handle queue position updates (format: "queue_update:position:wait_time")
                    elif "queue_update:" in response or "queue:" in response:
                        parts = response.split(":")
                        if len(parts) >= 3:
                            position = int(parts[1])
                            wait_minutes = int(parts[2])
                            
                            # Update UI elements
                            self.position_label.config(text=f"Your position in queue: {position}")
                            
                            if wait_minutes <= 1:
                                time_text = "Less than a minute"
                            else:
                                time_text = f"Approximately {wait_minutes} minutes"
                                
                            self.wait_time_label.config(text=f"Estimated wait time: {time_text}")
                            
                            # Update status message based on position
                            if position == 1:
                                status = "You're next! Almost there..."
                            else:
                                status = f"Please wait while we find a slot for you."
                            
                            self.status_label.config(text=status)
            except Exception as e:
                messagebox.showerror("Error", f"Connection lost: {e}")
        threading.Thread(target=check_status, daemon=True).start()

    def chat_window(self):
        """Display the chat window"""
        self.root.title("Chatroom")
        self.root.geometry("1000x600")  # Set the size of the chat window
        for widget in self.root.winfo_children():
            widget.destroy()

        # Create scrollable chat area - Composite pattern with ScrolledText
        self.chat_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD)
        self.chat_area.pack(expand=True, fill=tk.BOTH)
        self.chat_area.config(state="disabled") 

        threading.Thread(target=self.receive_messages, daemon=True).start()

        self.message_entry = tk.Entry(self.root)
        self.message_entry.pack(fill=tk.X, padx=10, pady=10)

        def send_file(self):
            pass  # to be done

        def send_message():
            """"send message to server"""
            message = self.message_entry.get()
            if message:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.client_socket.send(message.encode(FORMAT))
                self.chat_area.config(state="normal")
                self.chat_area.insert(tk.END, f"You [{timestamp}]: {message}\n")
                self.chat_area.config(state="disabled")
                self.chat_area.yview(tk.END)
                self.message_entry.delete(0, tk.END)
        self.send_button = tk.Button(self.root, text="Send", command=send_message)
        self.send_button.pack()

        self.file_button = tk.Button(self.root, text="Send File", command=send_file)
        self.file_button.pack()

        # Initialize the sound preference
        self.sound_var = tk.BooleanVar(value=False)
        # Create the checkbox with correct initial text
        self.sound_checkbox = tk.Checkbutton(
            self.root, 
            text="Unmute Sound", 
            variable=self.sound_var, 
            onvalue=True, 
            offvalue=False,
            command=self.toggle_sound
        )
        self.sound_checkbox = tk.Checkbutton(self.root, text="Unmute Sound", variable=self.sound_var, onvalue=True, offvalue=False,command=self.toggle_sound)
        self.sound_checkbox.pack(anchor='e', padx=10)

    def toggle_sound(self):
        """Toggle sound notification preference - Command pattern"""
        # Get the new state after the checkbox has been clicked
        new_state = self.sound_var.get() 
        # Send command to server
        self.client_socket.send("toggle_sound\n".encode(FORMAT))
        # Update checkbox text based on the new state
        if new_state:
            self.sound_checkbox.config(text="Mute Sound")
        else:
            self.sound_checkbox.config(text="Unmute Sound")
    

    def receive_messages(self):
        """Background thread to receive and display incoming messages"""
        while True:
            try:
                message = self.client_socket.recv(1024).decode(FORMAT)

                # Skip displaying sound toggle messages
                if "Sound enabled" in message or "Sound disabled" in message or "toggle_sound" in message:
                    continue

                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.chat_area.config(state="normal")
                self.chat_area.insert(tk.END, f"[{timestamp}] {message}\n")
                self.chat_area.config(state="disabled")
                self.chat_area.yview(tk.END)
            except Exception as e:
                print("[EXCEPTION] ", e)
                break

if __name__ == "__main__":
    root = tk.Tk()
    client = GUI(root)
    root.mainloop()