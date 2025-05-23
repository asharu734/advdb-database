from tkinter import *
from tkinter import ttk, messagebox
from tkinter import filedialog
import database
import requests

class App:
    def __init__(self):
        self.root = Tk()

        version = "0.0.11"
        self.root.title(f"Employee Payroll Management System v{version}")

        self.api_url = "http://localhost:5000/api"  # Change to server IP if needed

        self.init_ui()
        self.load_employees()


    def init_ui(self):
        self.init_heading()
        self.init_employee_view()
        self.init_buttons()
        
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

        Button(self.button_frame, text="Add...", command=self.add_employee) \
            .grid(row=0, column=0, padx=5)
        Button(self.button_frame, text="Edit", command=self.edit_employee) \
            .grid(row=0, column=1, padx=5)
        Button(self.button_frame, text="Delete", command=self.delete_employee) \
            .grid(row=0, column=2, padx=5)
        Button(self.button_frame, text="Ok", command=self.confirm_selection) \
            .grid(row=0, column=3, padx=5)
        Button(self.button_frame, text="View Attendance", command=self.view_attendance) \
            .grid(row=0, column=4, padx=5)


    def load_employees(self):
        try:
            response = requests.get(f"{self.api_url}/employees")
            if response.status_code == 200:
                employees = response.json()
                self.tree.delete(*self.tree.get_children())
                for emp in employees:
                    self.tree.insert("", "end", values=(
                        emp['employee_id'],
                        emp['firstname'],
                        emp['lastname'],
                        emp['daily_rate']
                    ))
            else:
                messagebox.showerror("Error", "Failed to load employees")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Connection Error", f"Could not connect to server: {e}")

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
            data = {
                "firstname": self.fname_entry.get(),
                "lastname": self.lname_entry.get(),
                "daily_rate": float(self.rate_entry.get())
            }
            try:
                response = requests.post(f"{self.api_url}/employees", json=data)
                if response.status_code == 201:
                    self.load_employees()  # Refresh the list
                    self.popup.destroy()
                else:
                    messagebox.showerror("Error", "Failed to add employee")
            except ValueError:
                messagebox.showerror("Error", "Daily rate must be a number")
            except requests.exceptions.RequestException as e:
                messagebox.showerror("Error", f"Server error: {e}")

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
        try:
            response = requests.get(f"{self.api_url}/employees/{employee_id}")
            if response.status_code != 200:
                messagebox.showerror("Error", "Employee not found")
                return
                
            emp_data = response.json()
        
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
        
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Could not connect to server: {e}")

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

            try:
                response = requests.delete(f"{self.api_url}/employees/{employee_id}")
                if response.status_code == 200:
                    self.load_employees()  # Refresh the list
                else:
                    messagebox.showerror("Error", "Failed to delete employee")
            except requests.exceptions.RequestException as e:
                messagebox.showerror("Error", f"Server error: {e}")


    def view_attendance(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Hmm", "Pick an employee first.")
            return

        emp_id = self.tree.item(selected[0], "values")[0]
        logs = [
            log for log in database.read_attendance_logs(self.cursor)
            if str(log[1]) == str(emp_id)
        ]

        popup = Toplevel(self.root)
        popup.title("Attendance Logs")

        tree = ttk.Treeview(popup, columns=("Project", "Date", "In", "Out", "Hours", "OT"), show="headings")
        for col in tree["columns"]:
            tree.heading(col, text=col)
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        for log in logs:
            project_id = log[2]
            # optiMight resolve project name from project_id
            project_name = f"#{project_id}"  # placeholder
            tree.insert("", "end", values=(project_name, log[6], log[3], log[4], log[7], log[5]))


if __name__ == "__main__":
    app = App()
    app.root.mainloop()
