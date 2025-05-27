from tkinter import Tk
from login import Login
from app import App

def start_app(token_data):
    login_root.destroy()
    token = token_data['token']
    role = token_data.get('role', 'admin')
    app = App(token, role)
    app.root.mainloop()

if __name__ == "__main__":
    login_root = Tk()
    Login(login_root, on_login_success=start_app)
    login_root.mainloop()