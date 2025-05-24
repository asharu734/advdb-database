from tkinter import *
from tkinter import Frame
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from config import api_base_url
import requests
import datetime

class ProjectManager(Frame):
    def __init__(self, parent, api_url, token):
        super().__init__(parent)
        self.token = token

        self.api_url = api_base_url

        self.init_ui()
        self.load_projects()


    def init_ui(self):
        Label(self, text="Project List").pack(pady=5)

        self.tree = ttk.Treeview(self, columns=("ID", "Name", "Start", "End", "Budget"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Name", text="Project Name")
        self.tree.heading("Start", text="Project Start")
        self.tree.heading("End", text="Project End")
        self.tree.heading("Budget", text="Budget")
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)

        btn_frame = Frame(self)
        btn_frame.pack(pady=10)

        Button(btn_frame, text="Add Project", command=self.add_project).grid(row=0, column=0, padx=5)
        Button(btn_frame, text="Delete Project", command=self.delete_project).grid(row=0, column=1, padx=5)
        Button(btn_frame, text="Manage Assignments", command=self.manage_assignments).grid(row=0, column=2, padx=5)

    def load_projects(self):
        try:
            response = requests.get(f"{self.api_url}/projects", headers={"Authorization": f"Bearer {self.token}"})
            if response.status_code == 200:
                self.tree.delete(*self.tree.get_children())
                for project in response.json():
                    self.tree.insert("", "end", values=(project['project_id'],
                                                        project['project_name'],
                                                        project['project_start'],
                                                        project['project_end'],
                                                        f"₱{project['budget']:,.2f}"))
            else:
                messagebox.showerror("Error", "Failed to load projects")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Could not connect to server: {e}")


    def add_project(self):
        self.popup = Toplevel(self.winfo_toplevel())
        self.popup.title("New Project")

        Label(self.popup, text="Project Name:").pack(pady=5)
        self.project_name_entry = Entry(self.popup)
        self.project_name_entry.pack(padx=10, pady=5)

        Label(self.popup, text="Project Start:").pack(pady=5)
        self.project_start_entry = DateEntry(self.popup, date_pattern='yyyy-mm-dd', mindate=datetime.date.today())
        self.project_start_entry.pack(padx=10, pady=5)

        Label(self.popup, text="Project End:").pack(pady=5)
        self.project_end_entry = DateEntry(self.popup, date_pattern='yyyy-mm-dd', mindate=datetime.date.today())
        self.project_end_entry.pack(padx=10, pady=5)

        Label(self.popup, text="Budget:").pack(pady=5)
        self.budget_entry = Entry(self.popup)
        self.budget_entry.pack(padx=10, pady=5)

        def save():
            name = self.project_name_entry.get().strip()
            start_date = self.project_start_entry.get_date()
            end_date = self.project_end_entry.get_date()
            budget = self.budget_entry.get() or 0  # Default to 0 if empty

            if not name:
                messagebox.showwarning("Oops", "Project name can't be empty")
                return
            
            if end_date < start_date:
                messagebox.showwarning("Error", "End date must be after start date!")
                return
            try:
                project_data = {
                    "project_name": name,
                    "project_start": start_date.isoformat(),
                    "project_end": end_date.isoformat(),
                    "budget": float(budget)
                }
                response = requests.post(f"{self.api_url}/projects", json=project_data, headers={"Authorization": f"Bearer {self.token}"})
                if response.status_code == 201:
                    self.load_projects()
                    self.popup.destroy()
                else:
                    messagebox.showerror("Error", "Failed to add project")
            except requests.exceptions.RequestException as e:
                messagebox.showerror("Error", f"Server error: {e}")

        Button(self.popup, text="Save", command=save).pack(pady=10)


    def delete_project(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Hmm", "Pick a project to delete")
            return

        project_id, name, *_ = self.tree.item(selected[0], "values")
        confirm = messagebox.askyesno("Sure?", f"Delete project '{name}'?")
        if confirm:
            try:
                response = requests.delete(f"{self.api_url}/projects/{project_id}", headers={"Authorization": f"Bearer {self.token}"})
                if response.status_code == 200:
                    self.load_projects()
                else:
                    messagebox.showerror("Error", "Failed to delete project")
            except requests.exceptions.RequestException as e:
                messagebox.showerror("Error", f"Server error: {e}")

    def manage_assignments(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a project first")
            return

        values = self.tree.item(selected[0], "values")
        project_id = values[0]
        project_name = values[1]  # Make sure your Treeview's second column is project name
        
        self.assign_popup = Toplevel(self.winfo_toplevel())
        self.assign_popup.title(f"Assign Employees to {project_name}")
        
        # Frame for assignment controls
        control_frame = Frame(self.assign_popup)
        control_frame.pack(pady=10)
        
        # Get all employees
        try:
            response = requests.get(f"{self.api_url}/employees", headers={"Authorization": f"Bearer {self.token}"})
            if response.status_code != 200:
                messagebox.showerror("Error", "Failed to load employees")
                return
            
            employees = response.json()
            
            # Employee selection dropdown
            Label(control_frame, text="Employee:").grid(row=0, column=0)
            self.employee_var = StringVar()
            self.employee_dropdown = ttk.Combobox(
                control_frame, 
                textvariable=self.employee_var,
                values=[f"{emp['employee_id']} - {emp['firstname']} {emp['lastname']}" for emp in employees]
            )
            self.employee_dropdown.grid(row=0, column=1, padx=5)
            
            # Date entry
            Label(control_frame, text="Date:").grid(row=1, column=0)
            self.date_entry = DateEntry(control_frame, date_pattern='yyyy-mm-dd')
            self.date_entry.grid(row=1, column=1, padx=5)
            
            # Time in/out
            Label(control_frame, text="Time In:").grid(row=2, column=0)
            self.time_in_entry = Entry(control_frame)
            self.time_in_entry.insert(0, "08:00")
            self.time_in_entry.grid(row=2, column=1, padx=5)
            
            Label(control_frame, text="Time Out:").grid(row=3, column=0)
            self.time_out_entry = Entry(control_frame)
            self.time_out_entry.insert(0, "17:00")
            self.time_out_entry.grid(row=3, column=1, padx=5)
            
            # Assignment button
            Button(control_frame, text="Assign", command=lambda: self.assign_employee(project_id)).grid(
                row=4, columnspan=2, pady=5
            )
            
            # List of current assignments
            assignments_frame = Frame(self.assign_popup)
            assignments_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            self.assignments_tree = ttk.Treeview(
                assignments_frame,
                columns=("Employee", "Date", "Time In", "Time Out", "Hours", "OT"),
                show="headings"
            )
            self.assignments_tree.heading("Employee", text="Employee")
            self.assignments_tree.heading("Date", text="Date")
            self.assignments_tree.heading("Time In", text="Time In")
            self.assignments_tree.heading("Time Out", text="Time Out")
            self.assignments_tree.heading("Hours", text="Hours")
            self.assignments_tree.heading("OT", text="Overtime")
            self.assignments_tree.pack(fill="both", expand=True)
            
            self.load_project_assignments(project_id)
            
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Could not connect to server: {e}")
        
    def load_project_assignments(self, project_id):
        try:
            response = requests.get(f"{self.api_url}/deployments/project/{project_id}", headers={"Authorization": f"Bearer {self.token}"})
            if response.status_code == 200:
                self.assignments_tree.delete(*self.assignments_tree.get_children())
                for assignment in response.json():
                    self.assignments_tree.insert("", "end", values=(
                        f"{assignment['firstname']} {assignment['lastname']}",
                        assignment['date'],
                        assignment['time_in'],
                        assignment['time_out'],
                        assignment['attendance_hours'],
                        assignment['overtime_hours']
                    ))
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Could not load assignments: {e}")

    def assign_employee(self, project_id):
        employee_str = self.employee_var.get()
        if not employee_str:
            messagebox.showwarning("Warning", "Please select an employee")
            return
        
        employee_id = int(employee_str.split(" - ")[0])
        date = self.date_entry.get_date().isoformat()
        time_in = self.time_in_entry.get()
        time_out = self.time_out_entry.get()
        
        try:
            response = requests.post(f"{self.api_url}/deployments", json={
                "employee_id": employee_id,
                "project_id": project_id,
                "time_in": time_in,
                "time_out": time_out,
                "date": date
            }, headers={"Authorization": f"Bearer {self.token}"})
            
            if response.status_code == 201:
                messagebox.showinfo("Success", "Employee assigned successfully")
                self.load_project_assignments(project_id)
            else:
                messagebox.showerror("Error", "Failed to assign employee")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Could not connect to server: {e}")