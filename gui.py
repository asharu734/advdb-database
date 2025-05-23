from tkinter import *
from tkinter import ttk, messagebox
from tkinter import filedialog
import database

class App:
    def __init__(self):
        self.root = Tk()

        version = "0.0.3"
        self.root.title(f"Employee Payroll Management System v{version}")

        self.db_name = "payroll.db" # Ano ilalagay dito
        self.conn = database.create_connection(self.db_name)
        self.cursor = self.conn.cursor()

        self.init_heading()
        self.init_employee_view()
        self.init_buttons()
        # self.load_employees()
        # This doesn't work yet


    def init_heading(self):
        self.heading = ttk.Label(
            self.root,
            text="Select Employee...")
        self.heading.pack(fill="x", padx=10, pady=5)

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

        Button(self.button_frame, text="Add...", command=self.add_employee).grid(row=0, column=0, padx=5)
        Button(self.button_frame, text="Edit").grid(row=0, column=1, padx=5)
        Button(self.button_frame, text="Delete").grid(row=0, column=2, padx=5)
        Button(self.button_frame, text="Ok").grid(row=0, column=3, padx=5)


    def load_employees(self):
        self.tree.delete(*self.tree.get_children())

        self.employees = database.read_employees(self.cursor)
        for employee_id, first, last, rate in self.employees:
            self.tree.insert("", "end", values=(employee_id, first, last, rate))

    
    def add_employee(self):
        self.popup = Toplevel(self.root)
        self.popup.title("New Employee")

        Label(self.popup, text="Enter Employee data...").grid(
            row=0, 
            column=0,
            padx=5,
            pady=10)

        Label(self.popup, text="First Name").grid(row=1, column=0)
        fname = Entry(self.popup)
        fname.grid(row=1, column=1, padx=5, pady=10)

        Label(self.popup, text="Last Name").grid(row=2, column=0)
        lname = Entry(self.popup)
        lname.grid(row=2, column=1, padx=5, pady=10)

        Label(self.popup, text="Daily Rate").grid(row=3, column=0)
        rate = Entry(self.popup)
        rate.grid(row=3, column=1, padx=5, pady=10)

        def save():
            pass 
            # Function in a function, wtf man

        Button(self.popup, text="Save", command=save).grid(
            row=4, 
            columnspan=2,
            pady=5
        )



if __name__ == "__main__":
    app = App()
    app.root.mainloop()
