from tkinter import *
from tkinter import messagebox
import requests
from main_config import api_base_url

class Login:
    def __init__(self, root, on_login_success):
        self.root = root
        self.on_login_success = on_login_success
        self.root.title("Login")
        self.root.geometry("300x200")

        self.frame = Frame(root, padx=10, pady=10)
        self.frame.pack(expand=True)

        Label(self.frame, text="Username:").grid(row=0, column=0, sticky=W)
        self.username_entry = Entry(self.frame)
        self.username_entry.grid(row=0, column=1)

        Label(self.frame, text="Password:").grid(row=1, column=0, sticky=W)
        self.password_entry = Entry(self.frame, show="*")
        self.password_entry.grid(row=1, column=1)

        self.login_btn = Button(self.frame, text="Login", command=self.login)
        self.login_btn.grid(row=2, column=0, columnspan=2, pady=10)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password.")
            return

        try:
            response = requests.post(
                f"{api_base_url}/login",
                json={'username': username, 'password': password}
            )
            if response.status_code == 200:
                token_data = response.json()
                self.on_login_success(token_data)
                self.frame.destroy()
            else:
                messagebox.showerror("Login Failed", "Invalid credentials.")
        except requests.RequestException as e:
            messagebox.showerror("Error", f"Could not connect to server.\n{e}")