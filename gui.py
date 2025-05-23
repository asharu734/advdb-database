from tkinter import *
from tkinter import ttk, messagebox
from tkinter import filedialog
import database

class App:
    def __init__(self):
        self.root = Tk()

        version = "0.0.11"
        self.root.title(f"Employee Payroll Management System v{version}")

        self.db_name = "payroll_app.db"
        self.conn = database.create_connection(self.db_name)
        if self.conn is None:
            messagebox.showerror("Error", "Could not connect to database")
            self.root.destroy()
            return
        
        self.cursor = self.conn.cursor()
        database.create_table(self.conn, self.cursor) #Ensures the table exists

        self.init_heading()
        self.init_employee_view()
        self.init_buttons()
        self.load_employees()


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
        Button(self.button_frame, text="Edit", command=self.edit_employee).grid(row=0, column=1, padx=5)
        Button(self.button_frame, text="Delete", command=self.delete_employee).grid(row=0, column=2, padx=5)
        Button(self.button_frame, text="Ok").grid(row=0, column=3, padx=5)


    def load_employees(self):
        try:
            self.tree.delete(*self.tree.get_children())
            employees = database.read_employees(self.cursor)

            if not employees:
                messagebox.showinfo("Info", "No employees found in database")
                return
            
            for employee in employees:
                self.tree.insert("", "end", values=employee)

        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to load employees: {str(e)}")

    def add_employee(self):
        self.popup = Toplevel(self.root)
        self.popup.title("New Employee")

        Label(self.popup, text="Enter Employee data...").grid(
            row=0, 
            column=0,
            padx=5,
            pady=10)

        Label(self.popup, text="First Name").grid(row=1, column=0)
        self.fname_entry = Entry(self.popup)
        self.fname_entry.grid(row=1, column=1, padx=5, pady=10)

        Label(self.popup, text="Last Name").grid(row=2, column=0)
        self.lname_entry = Entry(self.popup)
        self.lname_entry.grid(row=2, column=1, padx=5, pady=10)

        Label(self.popup, text="Daily Rate").grid(row=3, column=0)
        self.rate_entry = Entry(self.popup)
        self.rate_entry.grid(row=3, column=1, padx=5, pady=10)

        def save():
            firstname = self.fname_entry.get()
            lastname = self.lname_entry.get()
            try:
                daily_rate = float(self.rate_entry.get())
            except ValueError:
                messagebox.showerror("Error", "First and last name are required")
                return
            
            database.add_employee(self.conn, self.cursor, lastname, firstname, daily_rate)
            self.load_employees()
            self.popup.destroy()

        Button(self.popup, text="Save", command=save).grid(
            row=4, 
            columnspan=2,
            pady=5
        )
    
    def edit_employee(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an employee to edit")
            return
        
        employee_id = self.tree.item(selected[0])['values'][0]

        #Fetch current data
        self.cursor.execute("SELECT * FROM employee WHERE employee_id=?", (employee_id))
        emp_data = self.cursor.fetchone()

        if not emp_data:
            messagebox.showerror("Error", "Employee not found")
            return
        
        #Edit window
        self.edit_popup = Toplevel(self.root)
        self.edit_popup.title("Edit Employee")

        Label(self.edit_popup, text="Edit Employee Daya...").grid(
            row=0,
            column=0,
            padx=5,
            pady=10
        )

        Label(self.edit_popup, text="First Name").grid(row=1, column=0)
        fname_entry = Entry(self.edit_popup)
        fname_entry.insert(0, emp_data[2])
        fname_entry.grid(row=1, column=1, padx=5, pady=5)

        Label(self.edit_popup, text="Last Name").grid(row=1, column=0)
        lname_entry = Entry(self.edit_popup)
        lname_entry.insert(0, emp_data[1])
        lname_entry.grid(row=2, column=1, padx=5, pady=5)

        Label(self.edit_popup, text="Daily Rate").grid(row=1, column=0)
        rate_entry = Entry(self.edit_popup)
        rate_entry.insert(0, emp_data[3])
        rate_entry.grid(row=3, column=1, padx=5, pady=5)

        def save():
            new_first = fname_entry.get()
            new_last = lname_entry.get()
            try:
                new_rate = float(rate_entry.get())
            except ValueError:
                messagebox.showerror("Error", "Daily rate must be a number")
                return
            
            database.update_employees(self.conn, self.cursor, employee_id, new_last, new_first, new_rate)
            self.load_employees()
            self.edit_popup.destroy()

            Button(self.edit_popup, text="Save", command=save).grid(row=4, columnspan=2, pady=5)

    def delete_employee(self):
        selected= self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an employee to delete")
            return
        
        employee_id = self.tree.item(selected[0])['values'][0]

        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this employee?")

        if confirm:
            database.delete_employee(self.conn, self.cursor, employee_id)
            self.load_employees()

    def edit_employee(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Nah", "Pick an employee to edit.")

            return
        
        employee_id, first, last, rate = self.tree.item(selected[0], "values")

        self.popup = Toplevel(self.root)
        self.popup.title("Edit Employee")

        Label(self.popup, text="Edit Employee data...").grid(
            row=0, 
            column=0,
            padx=5,
            pady=10)

        Label(self.popup, text="First Name").grid(row=0, column=0)
        fname = Entry(self.popup)
        fname.insert(0, first)
        fname.grid(row=1, column=1, padx=5, pady=10)

        Label(self.popup, text="Last Name").grid(row=1, column=0)
        lname = Entry(self.popup)
        lname.insert(0, last)
        lname.grid(row=2, column=1, padx=5, pady=10)

        Label(self.popup, text="Daily Rate").grid(row=2, column=0)
        rate_entry = Entry(self.popup)
        rate_entry.insert(0, rate)
        rate_entry.grid(row=3, column=1, padx=5, pady=10)

        def save():
            try:
                database.update_employees(
                    self.conn, 
                    self.cursor, 
                    employee_id, 
                    lname.get(), 
                    fname.get(), 
                    float(rate_entry.get()))
                self.load_employees()
                self.popup.destroy()

            except ValueError:
                messagebox.showerror("Oops", "Missing info, duh.")

        Button(self.popup, text="Save", command=save).grid(
            row=4, 
            columnspan=2,
            pady=5
        )


    def delete_employee(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Nuh uh", "Pick an employee to delete.")

            return

        emp_id, first, last, *_ = self.tree.item(selected[0], "values")

        confirm = messagebox.askyesno("Confirm Delete", f"Delete {first} {last}?")
        if confirm:
            database.delete_employee(self.conn, self.cursor, emp_id)
            self.load_employees()


    def confirm_selection(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Hmm", "Select an employee, then hit Ok.")

            return
        
        emp_data = self.tree.item(selected[0], "values")
        print("Selected:", emp_data)  # placeholder
        messagebox.showinfo("Selection", f"You picked: {emp_data[1]} {emp_data[2]}")


if __name__ == "__main__":
    app = App()
    app.root.mainloop()
