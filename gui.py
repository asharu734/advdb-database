from tkinter import *
from tkinter import ttk, messagebox
from tkinter import filedialog

class App:
    def __init__(self):
        self.root = Tk()

        version = "0.0.3"
        self.root.title(f"Employee Payroll Management System v{version}")

        self.heading = ttk.Label(
            self.root,
            text="Select Employee...")
        self.heading.pack(fill="x", padx=10, pady=5)

        self.tree = self.init_employee_view()

        self.buttons = self.init_buttons()


    def init_employee_view(self):
        self.tree = ttk.Treeview(
            self.root,
            columns=("ID", "First", "Last", "Rate"),
            show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("First", text="First Name")
        self.tree.heading("Last", text="Surname")
        self.tree.heading("Rate", text="Daily Rate")
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)


    def init_buttons(self):
        self.button_frame = Frame(self.root)
        self.button_frame.pack(pady=10)

        Button(self.button_frame, text="Add...").grid(row=0, column=0, padx=5)
        Button(self.button_frame, text="Edit").grid(row=0, column=1, padx=5)
        Button(self.button_frame, text="Delete").grid(row=0, column=2, padx=5)
        Button(self.button_frame, text="Ok").grid(row=0, column=3, padx=5)


if __name__ == "__main__":
    app = App()
    app.root.mainloop()
