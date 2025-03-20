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
        except Exception as e:
            print(f"Error connecting to server: {e}")
            messagebox.showerror("Error", f"Error connecting to server: {e}")
            return

        self.username = None
        self.password = None
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.login_or_register()

    def on_closing(self):
        try:
            self.client_socket.close()
        except Exception as e:
            print(f"Error closing socket: {e}")
        finally:
            self.root.destroy()

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
            try:
                self.username = username_entry.get()
                self.password = password_entry.get()
                message = f"login\n{self.username}\n{self.password}\n"
                self.client_socket.sendall(message.encode(FORMAT))

                # Wait for the server's response
                response = self.client_socket.recv(1024).decode(FORMAT)
                if "success" in response.lower():
                    messagebox.showinfo("Success", "Login successful!")
                    self.chat_window()  # Open the chat window
                elif "queue" in response.lower():
                    self.queue_window(response)  # Open the queue window
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
                # Basic validation
                if not self.username or not self.password:
                    messagebox.showerror("Error", "Username and password cannot be empty!")
                    return
                print(f"Sending registration request for user username: {self.username}")
                print(f"Sending registration request for user password: {self.password}")
                message = f"register\n{self.username}\n{self.password}\n"
                self.client_socket.sendall(message.encode(FORMAT))

                # Wait for the server's response
                response = self.client_socket.recv(1024).decode(FORMAT)
                print(f"Registration response: {response}")
                if "success" in response.lower():
                    messagebox.showinfo("Success", "Registration successful!")
                    self.login_window()  # Open the login window
                else:
                    messagebox.showerror("Error", response)
            except Exception as e:
                print(f"Error during registration: {e}")
                messagebox.showerror("Error", f"Error during registration: {e}")
        tk.Button(self.root, text="Register", command=register).pack()
        tk.Button(self.root, text="Go back", command=self.login_or_register).pack()

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
        def send_file():
            pass

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
        self.send_button.pack(pady=10)
        self.send_button_file = tk.Button(self.root, text="Send file", command=send_file)
        self.send_button_file.pack(pady=10)


    def queue_window(self, response):
        self.root.title("Waiting Queue")
        self.root.geometry("400x300")  # Set appropriate window size
        for widget in self.root.winfo_children():
            widget.destroy()

        # Extract position and wait time from response
        import re
        position_match = re.search(r'position (\d+)', response)
        time_match = re.search(r'time: (\d+)', response)
        
        position = int(position_match.group(1)) if position_match else 0
        wait_time = int(time_match.group(1)) if time_match else 0
        
        # Create labels for information
        header_label = tk.Label(self.root, text="You are in the waiting queue", font=("Arial", 16))
        header_label.pack(pady=10)
        
        position_label = tk.Label(self.root, text=f"Your position: {position}", font=("Arial", 12))
        position_label.pack(pady=5)
        
        time_label = tk.Label(self.root, text=f"Estimated wait time: {wait_time} seconds", font=("Arial", 12))
        time_label.pack(pady=5)
        
        countdown_var = tk.StringVar(value=f"Time remaining: {wait_time} seconds")
        countdown_label = tk.Label(self.root, textvariable=countdown_var, font=("Arial", 12))
        countdown_label.pack(pady=10)
        
        status_var = tk.StringVar(value="Waiting for your turn...")
        status_label = tk.Label(self.root, textvariable=status_var, font=("Arial", 12))
        status_label.pack(pady=10)
        
        # Create countdown timer
        def update_countdown():
            nonlocal wait_time
            if wait_time > 0:
                wait_time -= 1
                countdown_var.set(f"Time remaining: {wait_time} seconds")
                self.root.after(1000, update_countdown)
            else:
                status_var.set("Attempting to connect...")
                try:
                    # Try to log in again after waiting
                    message = f"login\n{self.username}\n{self.password}\n"
                    self.client_socket.sendall(message.encode(FORMAT))
                    
                    response = self.client_socket.recv(1024).decode(FORMAT)
                    if "success" in response.lower():
                        messagebox.showinfo("Success", "Login successful!")
                        self.chat_window()  # Open the chat window
                    elif "queue" in response.lower():
                        messagebox.showinfo("Still Waiting", "Server is still full. Updating queue position.")
                        self.queue_window(response)  # Update queue window with new position
                    else:
                        messagebox.showerror("Error", "Failed to connect after waiting.")
                        self.login_window()  # Return to login window
                except Exception as e:
                    print(f"Error during queue connection: {e}")
                    messagebox.showerror("Error", f"Connection error: {e}")
                    self.login_window()  # Return to login window
        
        # Start the countdown
        self.root.after(1000, update_countdown)
    
    # Cancel button to exit queue
    def cancel_waiting(self):
        if messagebox.askyesno("Cancel Waiting", "Are you sure you want to exit the queue?"):
            self.login_window()  # Return to login window
    
        cancel_button = tk.Button(self.root, text="Cancel", command=self.cancel_waiting)
        cancel_button.pack(pady=15)

    def send_file(self):
        pass  # to be done

    def receive_messages(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode(FORMAT)
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.chat_area.config(state="normal")
                self.chat_area.insert(tk.END, f"{timestamp} [{message}]\n")
                self.chat_area.config(state="disabled")
                self.chat_area.yview(tk.END)
            except ConnectionResetError:
                print("Server forcibly closed the connection.")
                self.client_socket.close()
                self.root.after(0, self.show_disconnect_message)  # Notify user in the GUI
                break
            except Exception as e:
                print("[EXCEPTION] ", e)
                break

if __name__ == "__main__":
    root = tk.Tk()
    client = GUI(root)
    root.mainloop()