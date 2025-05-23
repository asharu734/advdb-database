from tkinter import *
from tkinter import ttk, messagebox
from tkinter import filedialog
from projects_view import ProjectManager
import database
import requests


class App:
    def __init__(self):
        self.root = Tk()

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        self.employee_tab = Frame(self.notebook)
        self.notebook.add(self.employee_tab, text="Employees")

        self.project_tab = ProjectManager(self.notebook, self.api_url)
        self.notebook.add(self.project_tab, text="Projects")

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
            self.employee_tab,
            text="Select Employee...")
        self.heading.pack(fill="x", padx=10, pady=5)


    def init_employee_view(self):
        self.tree = ttk.Treeview(
            self.employee_tab,
            columns=("ID", "First", "Last", "Rate"),
            show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("First", text="First Name")
        self.tree.heading("Last", text="Surname")
        self.tree.heading("Rate", text="Daily Rate")
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)


    def init_buttons(self):
        self.button_frame = Frame(self.employee_tab)
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
            .grid(row=1, column=0, padx=5)
        Button(self.button_frame, text="Calculate Payroll", command=self.calculate_payroll) \
            .grid(row=1, column=1, padx=5)
        Button(self.button_frame, text="Generate Pay Record", command=self.generate_pay_record) \
            .grid(row=1, column=2, padx=5)
        Button(self.button_frame, text="Pay History", command=self.view_pay_history) \
            .grid(row=1, column=3, padx=5)
        Button(
            self.button_frame, 
            text="Projects", 
            command=lambda: ProjectManager(self.root, self.api_url)) \
        .grid(row=2, column=0, padx=5)


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


    def calculate_payroll(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Oops", "Pick an employee first.")

            return

        emp_id, first, last, *_ = self.tree.item(selected[0], "values")

        self.popup = Toplevel(self.root)
        self.popup.title("Calculate Payroll")

        Label(self.popup, text=f"Payroll for {first} {last}").grid(
            row=0, column=0, columnspan=2, pady=10
        )

        Label(self.popup, text="Start Date (YYYY-MM-DD):").grid(row=1, column=0, sticky="e")
        start_date = Entry(self.popup)
        start_date.grid(row=1, column=1, padx=5, pady=5)

        Label(self.popup, text="End Date (YYYY-MM-DD):").grid(row=2, column=0, sticky="e")
        end_date = Entry(self.popup)
        end_date.grid(row=2, column=1, padx=5, pady=5)

        result_box = Text(self.popup, height=10, width=40, state="disabled")
        result_box.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

        def calculate():
            # Placeholder results – replace with real logic later
            results = f"""
    Employee: {first} {last}
    Start Date: {start_date.get()}
    End Date: {end_date.get()}
    Days Worked: ???
    Total Hours: ???
    Overtime: ???
    Gross Pay: ???
    Deductions: ???
    Net Pay: ???
    """
            result_box.config(state="normal")
            result_box.delete("1.0", END)
            result_box.insert("1.0", results)
            result_box.config(state="disabled")

        Button(self.popup, text="Calculate", command=calculate).grid(
            row=3, column=0, columnspan=2, pady=5
        )


    def generate_pay_record(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Wait", "Pick an employee first.")

            return

        emp_id, first, last, *_ = self.tree.item(selected[0], "values")

        self.popup = Toplevel(self.root)
        self.popup.title("Generate Pay Record")

        Label(self.popup, text=f"Generate Pay Record for {first} {last}").grid(
            row=0, column=0, columnspan=2, pady=10
        )

        Label(self.popup, text="Pay Period Start:").grid(row=1, column=0, sticky="e")
        start_date = Entry(self.popup)
        start_date.grid(row=1, column=1, padx=5, pady=5)

        Label(self.popup, text="Pay Period End:").grid(row=2, column=0, sticky="e")
        end_date = Entry(self.popup)
        end_date.grid(row=2, column=1, padx=5, pady=5)

        Label(self.popup, text="Gross Pay:").grid(row=3, column=0, sticky="e")
        gross = Entry(self.popup)
        gross.grid(row=3, column=1, padx=5, pady=5)

        Label(self.popup, text="Deductions:").grid(row=4, column=0, sticky="e")
        deductions = Entry(self.popup)
        deductions.grid(row=4, column=1, padx=5, pady=5)

        Label(self.popup, text="Net Pay:").grid(row=5, column=0, sticky="e")
        net = Entry(self.popup)
        net.grid(row=5, column=1, padx=5, pady=5)

        def save_record():
            # Placeholder — you’ll wire this into the DB later
            messagebox.showinfo("Saved!", "Pay record generated (kinda).")
            self.popup.destroy()

        Button(self.popup, text="Save Pay Record", command=save_record).grid(
            row=6, column=0, columnspan=2, pady=10
        )


    def view_pay_history(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Yo", "Pick an employee to view pay history.")

            return

        emp_id, first, last, *_ = self.tree.item(selected[0], "values")

        self.popup = Toplevel(self.root)
        self.popup.title(f"{first} {last} – Pay History")

        Label(self.popup, text=f"Payroll history for {first} {last}").pack(pady=10)

        history_tree = ttk.Treeview(self.popup, columns=("Start", "End", "Gross", "Deductions", "Net"), show="headings")
        history_tree.heading("Start", text="Start Date")
        history_tree.heading("End", text="End Date")
        history_tree.heading("Gross", text="Gross Pay")
        history_tree.heading("Deductions", text="Deductions")
        history_tree.heading("Net", text="Net Pay")
        history_tree.pack(fill="both", expand=True, padx=10, pady=10)

        # Placeholder: This will be replaced with real data from DB
        sample_data = [
            ("2024-05-01", "2024-05-15", 15000.00, 2000.00, 13000.00),
            ("2024-05-16", "2024-05-31", 16000.00, 1800.00, 14200.00),
        ]

        for row in sample_data:
            history_tree.insert("", "end", values=row)


if __name__ == "__main__":
    app = App()
    app.root.mainloop()
