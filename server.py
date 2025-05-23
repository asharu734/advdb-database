from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Database file path (use an absolute path)
DB_PATH = os.path.abspath("payroll_app.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn

# Initialize database tables (run once)
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.executescript('''
    CREATE TABLE IF NOT EXISTS EMPLOYEE (
        employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
        lastname TEXT NOT NULL,
        firstname TEXT NOT NULL,
        daily_rate REAL NOT NULL
    );
    CREATE TABLE IF NOT EXISTS PROJECT (
        project_id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_name TEXT NOT NULL
    );
    ''')
    conn.commit()
    conn.close()

# Employees API
@app.route('/api/employees', methods=['GET', 'POST'])
def employees():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'GET':
        cursor.execute("SELECT * FROM employee")
        employees = cursor.fetchall()
        conn.close()
        return jsonify([dict(row) for row in employees])

    elif request.method == 'POST':
        data = request.json
        cursor.execute(
            "INSERT INTO employee (lastname, firstname, daily_rate) VALUES (?, ?, ?)",
            (data['lastname'], data['firstname'], data['daily_rate'])
        )
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "id": cursor.lastrowid}), 201

# Project API
@app.route('/api/projects', methods=['GET', 'POST'])
def projects():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'GET':
        cursor.execute("SELECT * FROM project")
        employees = cursor.fetchall()
        conn.close()
        return jsonify([dict(row) for row in employees])
    
    elif request.method == 'POST':
        data = request.json
        cursor.execute(
            "INSERT INTO project (project_name) VALUES (?)",
            (data['project_name'])
        )
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "id": cursor.lastrowid}), 201

# Run the server
if __name__ == '__main__':
    init_db()  # Initialize tables if they don't exist
    app.run(host='0.0.0.0', port=5000, debug=True)