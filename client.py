import socket
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext
from authentication import login_to_DB, register_to_DB
#https://www.geeksforgeeks.org/python-gui-tkinter/
#https://www.geeksforgeeks.org/gui-chat-application-using-tkinter-in-python/
#https://docs.python.org/3/library/tkinter.html

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 7000
FORMAT= "utf-8"


class GUI:
    def __init__(self, root):
        self.root = root

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((SERVER_HOST, SERVER_PORT))

        self.username = None
        self.password = None
        
        self.login_or_register()

        def login_or_register(self):
            choice = tk.Toplevel(root)
            choice.title("Login/Register")
            tk.Label(choice, text="Do you want to login or register?").pack()

            def open_login():
                choice.destroy()
                self.login_window()

            def open_register():
                choice.destroy()
                self.register_window()
            tk.Button(choice, text="Login", command=open_login).pack()
            tk.Button(choice, text="Register", command=open_register).pack()


        def login_window(self):
            login_win = tk.Toplevel(root)
            login_win.title("Login")

            tk.Label(login_win, text="Username").pack()
            username_entry = tk.Entry(login)
            username_entry.username.pack()

            tk.Label(login_win, text="Password").pack()
            password_entry = tk.Entry(login_win, show="*")
            password_entry.pack()

            def login():
                self.username = username_entry.get()
                self.password = password_entry.get()
                self.client_socket.send("login".encode(FORMAT))  # Send action
                self.client_socket.send(self.username.encode(FORMAT))  # Send username
                self.client_socket.send(self.password.encode(FORMAT))  # Send password

                # Wait for the server's response
                response = self.client_socket.recv(1024).decode(FORMAT)
                if "success" in response.lower():
                    messagebox.showinfo("Success", "Login successful!")
                    login_win.destroy()
                    self.chat_window()  # Open the chat window
                else:
                    messagebox.showerror("Error", "Invalid credentials!")
            tk.Button(login, text="Login", command=login).pack()
        
        def register_window():
            register_win = tk.Toplevel(root)
            register_win.title("Register")

            tk.Label(register_win, text="Username").pack()
            username_entry = tk.Entry(register_win)
            username_entry.username.pack()

            tk.Label(register_win, text="Password").pack()
            password_entry = tk.Entry(register_win, show="*")
            password_entry.pack()

            def register():
                self.username = username_entry.get()
                self.password = password_entry.get()

                self.client_socket.send("register".encode(FORMAT))  # Send action
                self.client_socket.send(self.username.encode(FORMAT))  # Send username
                self.client_socket.send(self.password.encode(FORMAT))  # Send password

                # Wait for the server's response
                response = self.client_socket.recv(1024).decode(FORMAT)
                if "success" in response.lower():
                    messagebox.showinfo("Success", "Registration successful!")
                    register_win.destroy()
                    self.login_window()  # Open the chat window
                else:
                    messagebox.showerror("Error", "Invalid credentials!")
            tk.Button(register_win, text="Register", command=register).pack()

        def chat_window(self):
            self.chat_win = tk.Toplevel(root)
            self.chat_win.title("Chatroom")
            self.chat_are = scrolledtext.ScrolledText(self.chat_win)
            self.chat_area.pack()
            self.chat_area.config(state="disabled") 

            threading.Thread(target=self.receive_messages).start()

            self.message_entry = tk.Entry(self.chat_win)
            self.message_entry.pack()
            self.message_entry.bind("<Return>", self.send_message)

            self.send_button = tk.Button(self.chat_win, text="Send", command=self.send_message)
            self.send_button.pack()

            self.file_button = tk.Button(self.chat_win, text="Send File", command=self.send_file)
            self.file_button.pack()

        def send_message(self, event=None):
            message = self.message_entry.get()
            self.client_socket.send(message.encode(FORMAT))
            self.message_entry.delete(0, tk.END)

        def send_file(self):
            pass # to be done

        def receive_messages(self):
            while True:
                try:
                    message = self.client_socket.recv(1024).decode(FORMAT)
                    self.chat_area.config(state="normal")
                    self.chat_area.insert(tk.END, message + "\n")
                    self.chat_area.config(state="disabled")
                    self.chat_area.yview(tk.END)
                except Exception as e:
                    print("[EXCEPTION] ", e)
                    break

if __name__ == "__main__":
    root = tk.Tk()
    client = GUI(root)
    root.mainloop()