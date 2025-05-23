from tkinter import *
from tkinter import ttk, messagebox
import database
import requests

class ProjectManager:
    def __init__(self, root, api_url):
        self.api_url = api_url
        self.root = Toplevel(root)
        self.root.title("Manage Projects")

        self.init_ui()
        self.load_projects()


    def init_ui(self):
        Label(self.root, text="Project List").pack(pady=5)

        self.tree = ttk.Treeview(self.root, columns=("ID", "Name"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Name", text="Project Name")
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)

        btn_frame = Frame(self.root)
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
        popup = Toplevel(self.root)
        popup.title("New Project")

        Label(popup, text="Project Name:").pack(pady=5)
        entry = Entry(popup)
        entry.pack(padx=10, pady=5)

        def save():
            name = entry.get().strip()
            if not name:
                messagebox.showwarning("Oops", "Project name can't be empty")
                return
            try:
                response = requests.post(f"{self.api_url}/projects", json={"project_name": name})
                if response.status_code == 201:
                    self.load_projects()
                    popup.destroy()
                else:
                    messagebox.showerror("Error", "Failed to add project")
            except requests.exceptions.RequestException as e:
                messagebox.showerror("Error", f"Server error: {e}")

        Button(popup, text="Save", command=save).pack(pady=10)


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