from tkinter import *
from tkinter import ttk, messagebox, Toplevel
from tkcalendar import DateEntry
import requests
from main_config import api_base_url
from projects_view import ProjectManager
from user_creation import UserCreationWindow
from datetime import datetime

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

        self.project_tab = ProjectManager(self.notebook, self.api_url, self.token)
        self.notebook.add(self.project_tab, text="Projects")

        version = "0.0.27"
        self.root.title(f"Employee Payroll Management System v{version}")

        self.init_ui()
        ttk.Label(self.root, text=f"Logged in as role: {role}").pack(pady=10)
        self.load_employees()

        if self.role == 'super_admin':
            ttk.Button(self.root, text="Create New User", command=self.open_user_creation).pack(pady=10)

    def init_ui(self):
        self.init_employee_view()
        self.init_buttons()

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
        Button(self.button_frame, text="View Pay Record", command=self.view_pay_record) \
            .grid(row=1, column=2, padx=5)

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

        try:
            response = requests.get(
                f"{self.api_url}/employees/{employee_id}",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            if response.status_code != 200:
                messagebox.showerror("Error", "Employee not found")
                return

            emp_data = response.json()

            self.edit_popup = Toplevel(self.root)
            self.edit_popup.title("Edit Employee")

            Label(self.edit_popup, text="First Name").grid(row=0, column=0)
            fname_entry = Entry(self.edit_popup)
            fname_entry.insert(0, emp_data["firstname"])
            fname_entry.grid(row=0, column=1, padx=5, pady=5)

            Label(self.edit_popup, text="Last Name").grid(row=1, column=0)
            lname_entry = Entry(self.edit_popup)
            lname_entry.insert(0, emp_data["lastname"])
            lname_entry.grid(row=1, column=1, padx=5, pady=5)

            Label(self.edit_popup, text="Daily Rate").grid(row=2, column=0)
            rate_entry = Entry(self.edit_popup)
            rate_entry.insert(0, emp_data["daily_rate"])
            rate_entry.grid(row=2, column=1, padx=5, pady=5)

            def save():
                new_first = fname_entry.get()
                new_last = lname_entry.get()
                try:
                    new_rate = float(rate_entry.get())
                except ValueError:
                    messagebox.showerror("Error", "Daily rate must be a number")
                    return

                update_data = {
                    "firstname": new_first,
                    "lastname": new_last,
                    "daily_rate": new_rate
                }

                try:
                    update_response = requests.put(
                        f"{self.api_url}/employees/{employee_id}",
                        headers={
                            "Authorization": f"Bearer {self.token}",
                            "Content-Type": "application/json"
                        },
                        json=update_data
                    )

                    if update_response.status_code == 200:
                        self.load_employees()
                        self.edit_popup.destroy()
                    else:
                        messagebox.showerror("Error", "Failed to update employee")

                except requests.exceptions.RequestException as e:
                    messagebox.showerror("Error", f"Server error: {e}")

            Button(self.edit_popup, text="Save", command=save).grid(row=3, columnspan=2, pady=10)

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
            # First save the payroll record
            response = requests.post(
                f"{self.api_url}/payroll",
                headers={"Authorization": f"Bearer {self.token}"},
                json=self._current_payroll_calc
            )
            
            if response.status_code == 201:
                payroll_data = response.json()
                
                # Create a pay record associated with this payroll
                pay_record_data = {
                    'employee_id': emp_id,
                    'date_paid': datetime.now().strftime('%Y-%m-%d'),  # Current date
                    'amount': self._current_payroll_calc['net_salary'],
                    'reference_number': f"PY{datetime.now().strftime('%Y%m%d%H%M%S')}"  # Unique reference
                }
                
                pay_record_response = requests.post(
                    f"{self.api_url}/payrecords",
                    headers={"Authorization": f"Bearer {self.token}"},
                    json=pay_record_data
                )
                
                if pay_record_response.status_code == 201:
                    messagebox.showinfo("Success", "Payroll and payment records saved successfully")
                    self.payroll_popup.destroy()
                else:
                    messagebox.showerror("Error", f"Payroll saved but payment record failed: {pay_record_response.text}")
            else:
                messagebox.showerror("Error", f"Failed to save payroll record: {response.text}")
                
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Server error: {e}")
    
    def view_pay_record(self):
        if not self.token:
            messagebox.showerror("Error", "You must be logged in to view pay records.")
            return

        headers = {
            "Authorization": f"Bearer {self.token}"
        }

        try:
            response = requests.get(f"{self.api_url}/payrecords", headers=headers)
            if response.status_code == 200:
                records = response.json()

                # Create a new window
                window = Toplevel(self.root)
                window.title("Pay Records")
                window.geometry("800x400")

                # Create Treeview
                cols = ("Pay ID", "Employee", "Date Paid", "Amount", "Reference No.")
                tree = ttk.Treeview(window, columns=cols, show="headings")

                for col in cols:
                    tree.heading(col, text=col)
                    tree.column(col, width=150)

                for record in records:
                    employee_name = f"{record['firstname']} {record['lastname']}"
                    tree.insert("", "end", values=(
                        record["pay_id"],
                        employee_name,
                        record["date_paid"],
                        f"₱{record['amount']:,.2f}",
                        record["reference_number"]
                    ))

                    tree.pack(fill="both", expand=True, padx=10, pady=10)

            else:
                messagebox.showerror("Error", f"Failed to fetch records: {response.text}")
        except requests.RequestException as e:
                messagebox.showerror("Error", f"Request failed: {str(e)}")
        
    def open_user_creation(self):
        UserCreationWindow(self.root, api_url=api_base_url, token=self.token)