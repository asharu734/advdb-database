from tkinter import *
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from config import api_base_url
from projects_view import ProjectManager
import database
import requests


class App:
    def __init__(self, token, role):
        self.token = token
        self.role = role

        self.root = Tk()
        self.api_url = api_base_url

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        self.employee_tab = Frame(self.notebook)
        self.notebook.add(self.employee_tab, text="Employees")

        self.project_tab = ProjectManager(self.notebook, self.api_url)
        self.notebook.add(self.project_tab, text="Projects")

        version = "0.0.27"
        self.root.title(f"Employee Payroll Management System v{version}")

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
        Button(self.button_frame, text="Project Assignments", command=self.view_project_assignments) \
            .grid(row=0, column=3, padx=5)
        Button(self.button_frame, text="Calculate Payroll", command=self.calculate_payroll) \
            .grid(row=1, column=1, padx=5)
        Button(self.button_frame, text="Generate Pay Record", command=self.generate_pay_record) \
            .grid(row=1, column=2, padx=5)
        Button(self.button_frame, text="Pay History", command=self.view_pay_history) \
            .grid(row=1, column=3, padx=5)


    def load_employees(self):
        try:
            response = requests.get(f"{self.api_url}/employees", headers={"Authorization": f"Bearer {self.token}"})
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
                response = requests.post(f"{self.api_url}/employees", json=data, headers={"Authorization": f"Bearer {self.token}"})
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
            response = requests.get(f"{self.api_url}/employees", headers={"Authorization": f"Bearer {self.token}"})
            if response.status_code != 200:
                messagebox.showerror("Error", "Employee not found")
                return
                
            emp_data = response.json()
        
            #Edit window
            self.edit_popup = Toplevel(self.root)
            self.edit_popup.title("Edit Employee")

            Label(self.edit_popup, text="Edit Employee Data...").grid(
                row=0,
                column=0,
                padx=5,
                pady=10
            )

            Label(self.edit_popup, text="First Name").grid(row=1, column=0)
            fname_entry = Entry(self.edit_popup)
            fname_entry.insert(0, emp_data[2])
            fname_entry.grid(row=1, column=1, padx=5, pady=5)

            Label(self.edit_popup, text="Last Name").grid(row=2, column=0)
            lname_entry = Entry(self.edit_popup)
            lname_entry.insert(0, emp_data[1])
            lname_entry.grid(row=2, column=1, padx=5, pady=5)

            Label(self.edit_popup, text="Daily Rate").grid(row=3, column=0)
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
            try:
                response = requests.delete(f"{self.api_url}/employees/{employee_id}", headers={"Authorization": f"Bearer {self.token}"})
                if response.status_code == 200:
                    self.load_employees()  # Refresh the list
                else:
                    messagebox.showerror("Error", "Failed to delete employee")
            except requests.exceptions.RequestException as e:
                messagebox.showerror("Error", f"Server error: {e}")

    def view_project_assignments(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an employee first")
            return
        
        employee_id, first, last, _ = self.tree.item(selected[0], "values")
        
        popup = Toplevel(self.root)
        popup.title(f"{first} {last} - Project Assignments")
        
        try:
            response = requests.get(f"{self.api_url}/deployments/employee/{employee_id}", headers={"Authorization": f"Bearer {self.token}"})
            if response.status_code != 200:
                messagebox.showerror("Error", "Failed to load assignments")
                return
            
            tree = ttk.Treeview(popup, columns=("Project", "Date", "Time In", "Time Out", "Hours", "OT"), show="headings")
            tree.heading("Project", text="Project")
            tree.heading("Date", text="Date")
            tree.heading("Time In", text="Time In")
            tree.heading("Time Out", text="Time Out")
            tree.heading("Hours", text="Hours")
            tree.heading("OT", text="Overtime")
            tree.pack(fill="both", expand=True, padx=10, pady=10)
            
            for assignment in response.json():
                tree.insert("", "end", values=(
                    assignment['project_name'],
                    assignment['date'],
                    assignment['time_in'],
                    assignment['time_out'],
                    assignment['attendance_hours'],
                    assignment['overtime_hours']
                ))
                
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Could not connect to server: {e}")

    def calculate_payroll(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an employee first")
            return

        emp_id, first, last, daily_rate = self.tree.item(selected[0], "values")

        self.payroll_popup = Toplevel(self.root)
        self.payroll_popup.title(f"Payroll Calculation - {first} {last}")
        self.payroll_popup.geometry("500x600")

        # Input Frame
        input_frame = Frame(self.payroll_popup)
        input_frame.pack(pady=10)

        Label(input_frame, text=f"Payroll for {first} {last} (Rate: ₱{daily_rate}/day)").grid(
            row=0, column=0, columnspan=2, pady=10
        )

        # Date Range
        Label(input_frame, text="Start Date (YYYY-MM-DD):").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.start_date_entry = DateEntry(input_frame, date_pattern='yyyy-mm-dd')
        self.start_date_entry.grid(row=1, column=1, padx=5, pady=5)

        Label(input_frame, text="End Date (YYYY-MM-DD):").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.end_date_entry = DateEntry(input_frame, date_pattern='yyyy-mm-dd')
        self.end_date_entry.grid(row=2, column=1, padx=5, pady=5)

        # Deductions
        Label(input_frame, text="Deductions:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        self.deductions_entry = Entry(input_frame)
        self.deductions_entry.insert(0, "0")
        self.deductions_entry.grid(row=3, column=1, padx=5, pady=5)

        # Calculate Button
        Button(input_frame, text="Calculate Payroll", command=lambda: self._perform_payroll_calculation(
            emp_id, first, last, daily_rate
        )).grid(row=4, columnspan=2, pady=10)

        # Results Frame
        results_frame = Frame(self.payroll_popup)
        results_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.results_text = Text(results_frame, height=15, width=60, state="disabled")
        self.results_text.pack(fill="both", expand=True)

        # Save Button
        Button(self.payroll_popup, text="Save Payroll Record", 
            command=lambda: self._save_payroll_record(emp_id)).pack(pady=10)

    def _perform_payroll_calculation(self, emp_id, first, last, daily_rate):
        try:
            start_date = self.start_date_entry.get_date().isoformat()
            end_date = self.end_date_entry.get_date().isoformat()
            deductions = float(self.deductions_entry.get())
            
            # Get time logs for the period
            response = requests.get(
                f"{self.api_url}/deployments/employee/{emp_id}",
                headers={"Authorization": f"Bearer {self.token}"},
                params={"start_date": start_date, "end_date": end_date}
            )
            
            if response.status_code != 200:
                messagebox.showerror("Error", "Failed to fetch time logs")
                return
                
            time_logs = response.json()
            
            if not time_logs:
                messagebox.showinfo("Info", "No time logs found for this period")
                return
                
            # Calculate totals
            total_days = len({log['date'] for log in time_logs})
            total_hours = sum(log['attendance_hours'] for log in time_logs)
            total_ot = sum(log['overtime_hours'] for log in time_logs)
            
            # Calculate pay
            daily_rate = float(daily_rate)
            regular_pay = total_days * daily_rate
            ot_pay = total_ot * (daily_rate / 8 * 1.25)  # Assuming 1.25x OT rate
            gross_pay = regular_pay + ot_pay
            net_pay = gross_pay - deductions
            
            # Format results
            results = f"""
            PAYROLL CALCULATION REPORT
            =========================
            Employee: {first} {last}
            Employee ID: {emp_id}
            Period: {start_date} to {end_date}
            
            ------------
            WORK SUMMARY
            ------------
            Days Worked: {total_days}
            Total Hours: {total_hours:.2f}
            Overtime Hours: {total_ot:.2f}
            
            ---------
            EARNINGS
            ---------
            Regular Pay ({total_days} days × ₱{daily_rate}): ₱{regular_pay:,.2f}
            Overtime Pay: ₱{ot_pay:,.2f}
            Gross Pay: ₱{gross_pay:,.2f}
            
            -----------
            DEDUCTIONS
            -----------
            Total Deductions: ₱{deductions:,.2f}
            
            --------
            NET PAY
            --------
            Net Pay: ₱{net_pay:,.2f}
            """
            
            # Store calculations for saving later
            self._current_payroll_calc = {
                "employee_id": emp_id,
                "gross_salary": gross_pay,
                "net_salary": net_pay,
                "week_start": start_date,
                "week_end": end_date,
                "deductions": deductions
            }
            
            # Display results
            self.results_text.config(state="normal")
            self.results_text.delete("1.0", END)
            self.results_text.insert("1.0", results)
            self.results_text.config(state="disabled")
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {e}")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Server error: {e}")

    def _save_payroll_record(self, emp_id):
        if not hasattr(self, '_current_payroll_calc'):
            messagebox.showwarning("Warning", "Please calculate payroll first")
            return
            
        try:
            # Save to database
            response = requests.post(
                f"{self.api_url}/payroll",
                headers={"Authorization": f"Bearer {self.token}"},
                json=self._current_payroll_calc
            )
            
            if response.status_code == 201:
                messagebox.showinfo("Success", "Payroll record saved successfully")
                self.payroll_popup.destroy()
            else:
                messagebox.showerror("Error", "Failed to save payroll record")
                
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Server error: {e}")
    
    def generate_pay_record(self):
        print("Generate Pay Record button clicked.") # Placeholder -J

    def view_pay_history(self):
        print("Generate Pay Record button clicked.")

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

if __name__ == "__main__":
    login_root = Tk()

    def start_app(token_data):
        login_root.destroy()  # Close the login window
        token = token_data['token']
        role = token_data.get('role', 'admin')

        app = App(token, role)  # Pass token and role
        app.root.mainloop()

    Login(login_root, on_login_success=start_app)
    login_root.mainloop()

