import socket
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext
from datetime import datetime
#https://www.geeksforgeeks.org/python-gui-tkinter/
#https://www.geeksforgeeks.org/gui-chat-application-using-tkinter-in-python/
#https://docs.python.org/3/library/tkinter.html

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 7000
FORMAT = "utf-8"

class GUI:
    def __init__(self, root):
        self.root = root
        self.root.geometry("250x250")
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((SERVER_HOST, SERVER_PORT))
            response = self.client_socket.recv(1024).decode(FORMAT)
            if response == "queue":
                self.waiting_window()
            else:
                self.login_or_register()
        except Exception as e:
            print(f"Error connecting to server: {e}")
            messagebox.showerror("Error", f"Error connecting to server: {e}")
            return

    def login_or_register(self):
        self.root.title("Login/Register")
        for widget in self.root.winfo_children():
            widget.destroy()
        tk.Label(self.root, text="Do you want to login or register?").pack()
        tk.Button(self.root, text="Login", command=self.login_window).pack()
        tk.Button(self.root, text="Register", command=self.register_window).pack()


    def login_window(self):
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
        self.root.title("Waiting Room")
        for widget in self.root.winfo_children():
            widget.destroy()
        tk.Label(self.root, text="You are in the queue. Please wait...").pack()
        self.wait_label = tk.Label(self.root, text="Checking status...")
        self.wait_label.pack()
        def check_status():
            try:
                while True:
                    response = self.client_socket.recv(1024).decode(FORMAT)
                    print(response, "queeu")
                    if "welcome" in response.lower():
                        messagebox.showinfo("Access Granted", "You can use the chat!")
                        self.login_or_register()
                        break
            except Exception as e:
                messagebox.showerror("Error", f"Connection lost: {e}")
        threading.Thread(target=check_status, daemon=True).start()

    def chat_window(self):
        self.root.title("Chatroom")
        self.root.geometry("1000x600")  # Set the size of the chat window
        for widget in self.root.winfo_children():
            widget.destroy()

        self.chat_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD)
        self.chat_area.pack(expand=True, fill=tk.BOTH)
        self.chat_area.config(state="disabled") 

        threading.Thread(target=self.receive_messages, daemon=True).start()

        self.message_entry = tk.Entry(self.root)
        self.message_entry.pack(fill=tk.X, padx=10, pady=10)

        def send_file(self):
            pass  # to be done

        def send_message():
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
        self.sound_checkbox.pack(anchor='e', padx=10)

    def toggle_sound(self):
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