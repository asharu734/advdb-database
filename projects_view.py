from tkinter import *
from tkinter import Frame
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from config import api_base_url
import requests
import datetime

class ProjectManager(Frame):
    def __init__(self, parent, api_url):
        super().__init__(parent)

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


    def load_projects(self):
        try:
            response = requests.get(f"{self.api_url}/projects")
            if response.status_code == 200:
                self.tree.delete(*self.tree.get_children())
                for project in response.json():
                    self.tree.insert("", "end", values=(project['project_id'], project['project_name']))
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
                response = requests.post(f"{self.api_url}/projects", json=project_data)
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

        project_id, name = self.tree.item(selected[0], "values")
        confirm = messagebox.askyesno("Sure?", f"Delete project '{name}'?")
        if confirm:
            try:
                response = requests.delete(f"{self.api_url}/projects/{project_id}")
                if response.status_code == 200:
                    self.load_projects()
                else:
                    messagebox.showerror("Error", "Failed to delete project")
            except requests.exceptions.RequestException as e:
                messagebox.showerror("Error", f"Server error: {e}")