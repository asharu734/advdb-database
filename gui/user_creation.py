import tkinter as tk
from tkinter import ttk, messagebox
import requests

class UserCreationWindow(tk.Toplevel):
    def __init__(self, parent, api_url, token):
        super().__init__(parent)
        self.api_url = api_url
        self.token = token
        self.title("Create New User")

        ttk.Label(self, text="Username:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.username_entry = ttk.Entry(self)
        self.username_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self, text="Password:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.password_entry = ttk.Entry(self, show="*")
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(self, text="Role:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.role_var = tk.StringVar()
        self.role_combobox = ttk.Combobox(self, textvariable=self.role_var, state="readonly")
        self.role_combobox['values'] = ('admin', 'super_admin')
        self.role_combobox.current(0)
        self.role_combobox.grid(row=2, column=1, padx=5, pady=5)

        ttk.Button(self, text="Create User", command=self.create_user).grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

    def create_user(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        role = self.role_var.get()

        if not username or not password or role not in ['admin', 'super_admin']:
            messagebox.showerror("Input Error", "Please fill all fields with valid data.")
            return

        data = {
            "username": username,
            "password": password,
            "role": role
        }

        try:
            response = requests.post(
                f"{self.api_url}/users",
                json=data,
                headers={"Authorization": f"Bearer {self.token}"}
            )
            if response.status_code == 201:
                messagebox.showinfo("Success", f"User '{username}' created successfully!")
                self.username_entry.delete(0, tk.END)
                self.password_entry.delete(0, tk.END)
                self.role_combobox.current(0)
            elif response.status_code == 409:
                messagebox.showerror("Error", "Username already exists.")
            else:
                messagebox.showerror("Error", f"Failed to create user: {response.text}")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Server error: {e}")