from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime


app = Flask(__name__)
CORS(app)

# Database configuration
DB_PATH = os.path.abspath("payroll_app.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

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
        project_name TEXT NOT NULL,
        project_start DATE NOT NULL,
        project_end DATE,
        budget REAL
    );

    CREATE TABLE IF NOT EXISTS DEPLOYMENT_LIST (
        employee_id INTEGER NOT NULL,
        project_id INTEGER NOT NULL,
        time_in TIME NOT NULL,
        time_out TIME NOT NULL,
        overtime_hours REAL DEFAULT 0,
        date DATE NOT NULL,
        attendance_hours REAL,
        PRIMARY KEY(employee_id, project_id, date),
        FOREIGN KEY (employee_id) REFERENCES EMPLOYEE(employee_id),
        FOREIGN KEY (project_id) REFERENCES PROJECT(project_id)
    );

    CREATE TABLE IF NOT EXISTS DEDUCTION (
        deduction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        deduction_type TEXT NOT NULL,
        FOREIGN KEY (employee_id) REFERENCES EMPLOYEE(employee_id)
    );

    CREATE TABLE IF NOT EXISTS PAYROLL (
        payroll_id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        gross_salary REAL NOT NULL,
        net_salary REAL NOT NULL,
        week_start DATE NOT NULL,
        week_end DATE NOT NULL,
        FOREIGN KEY (employee_id) REFERENCES EMPLOYEE(employee_id)
    );

    CREATE TABLE IF NOT EXISTS PAYROLL_DEDUCTION (
        payroll_id INTEGER NOT NULL,
        deduction_id INTEGER NOT NULL,
        deduction_amount REAL NOT NULL,
        PRIMARY KEY(payroll_id, deduction_id),
        FOREIGN KEY (payroll_id) REFERENCES PAYROLL(payroll_id),
        FOREIGN KEY (deduction_id) REFERENCES DEDUCTION(deduction_id)
    );
                
    CREATE TABLE IF NOT EXISTS PAY_RECORD (
        pay_id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        date_paid DATE NOT NULL,
        amount REAL NOT NULL,
        reference_number INTEGER NOT NULL,
        FOREIGN KEY (employee_id) REFERENCES EMPLOYEE(employee_id)
    );
    ''')
    conn.commit()
    conn.close()

# Helper function to compute attendance hours
def compute_attendance_hours(time_in_str, time_out_str):
    time_format = "%H:%M"
    time_in = datetime.strptime(time_in_str, time_format).time()
    time_out = datetime.strptime(time_out_str, time_format).time()
    
    if time_out <= time_in:
        raise ValueError("Time out must be after time in")
    
    total_seconds = (datetime.combine(datetime.today(), time_out) - 
                    datetime.combine(datetime.today(), time_in)).total_seconds()
    return total_seconds / 3600

# EMPLOYEE ENDPOINTS
@app.route('/api/employees', methods=['GET', 'POST'])
def employees():
    conn = get_db_connection()
    try:
        if request.method == 'GET':
            employees = conn.execute('SELECT * FROM employee').fetchall()
            return jsonify([dict(row) for row in employees])
        
        elif request.method == 'POST':
            data = request.json
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO employee (lastname, firstname, daily_rate) VALUES (?, ?, ?)',
                (data['lastname'], data['firstname'], data['daily_rate'])
            )
            conn.commit()
            return jsonify({
                'id': cursor.lastrowid,
                'lastname': data['lastname'],
                'firstname': data['firstname'],
                'daily_rate': data['daily_rate']
            }), 201
    finally:
        conn.close()

@app.route('/api/employees/<int:employee_id>', methods=['DELETE'])
def delete_employee(employee_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM employee WHERE employee_id = ?", (employee_id,))
    conn.commit()
    affected_rows = cursor.rowcount
    conn.close()
    
    if affected_rows > 0:
        return jsonify({"status": "success"}), 200
    else:
        return jsonify({"error": "Employee not found"}), 404

# PROJECT ENDPOINTS
@app.route('/api/projects', methods=['GET', 'POST'])
def projects():
    conn = get_db_connection()
    try:
        if request.method == 'GET':
            projects = conn.execute('SELECT * FROM project').fetchall()
            return jsonify([dict(row) for row in projects])
        
        elif request.method == 'POST':
            data = request.json
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT INTO project 
                (project_name, project_start, project_end, budget) 
                VALUES (?, ?, ?, ?)''',
                (data['project_name'], data.get('project_start'), 
                 data.get('project_end'), data.get('budget', 0))
            )
            conn.commit()
            return jsonify({
                'project_id': cursor.lastrowid,
                'project_name': data['project_name']
            }), 201
    finally:
        conn.close()

@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM project WHERE project_id = ?", (project_id,))
    conn.commit()
    affected_rows = cursor.rowcount
    conn.close()
    
    if affected_rows > 0:
        return jsonify({"status": "success"}), 200
    else:
        return jsonify({"error": "Project not found"}), 404

# DEPLOYMENT ENDPOINTS
@app.route('/api/deployments/employee/<int:employee_id>', methods=['GET'])
def get_employee_deployments(employee_id):
    conn = get_db_connection()
    try:
        deployments = conn.execute('''
            SELECT d.*, p.project_name
            FROM deployment_list d
            JOIN project p ON d.project_id = p.project_id
            WHERE d.employee_id = ?
        ''', (employee_id,)).fetchall()
        return jsonify([dict(row) for row in deployments])
    finally:
        conn.close()

@app.route('/api/deployments', methods=['POST'])
def add_deployment():
    data = request.json
    try:
        attendance_hours = compute_attendance_hours(data['time_in'], data['time_out'])
        overtime = max(0, attendance_hours - 8)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO deployment_list 
            (employee_id, project_id, time_in, time_out, 
             overtime_hours, date, attendance_hours)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (data['employee_id'], data['project_id'], 
             data['time_in'], data['time_out'], 
             overtime, data['date'], attendance_hours))
        conn.commit()
        return jsonify({'status': 'success'}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/deployments/project/<int:project_id>', methods=['GET'])
def get_project_deployments(project_id):
    conn = get_db_connection()
    try:
        deployments = conn.execute('''
            SELECT d.*, e.firstname, e.lastname
            FROM deployment_list d
            JOIN employee e ON d.employee_id = e.employee_id
            WHERE d.project_id = ?
        ''', (project_id,)).fetchall()
        return jsonify([dict(row) for row in deployments])
    finally:
        conn.close()

@app.route('/api/deployments/employee/<int:employee_id>')
def get_employee_deployments_filtered(employee_id):
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = '''
        SELECT d.*, p.project_name
        FROM deployment_list d
        JOIN project p ON d.project_id = p.project_id
        WHERE d.employee_id = ?
    '''
    params = [employee_id]
    
    if start_date and end_date:
        query += ' AND date BETWEEN ? AND ?'
        params.extend([start_date, end_date])
    
    conn = get_db_connection()
    deployments = conn.execute(query, params).fetchall()
    conn.close()
    return jsonify([dict(row) for row in deployments])

# PAYROLL ENDPOINTS
@app.route('/api/payroll', methods=['POST'])
def create_payroll():
    data = request.json
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Create payroll record
        cursor.execute('''
            INSERT INTO payroll 
            (employee_id, gross_salary, net_salary, week_start, week_end)
            VALUES (?, ?, ?, ?, ?)
        ''', (data['employee_id'], data['gross_salary'], 
             data['net_salary'], data['week_start'], data['week_end']))
        
        payroll_id = cursor.lastrowid
        
        # Add payroll deductions if any
        for deduction in data.get('deductions', []):
            cursor.execute('''
                INSERT INTO payroll_deduction 
                (payroll_id, deduction_id, deduction_amount)
                VALUES (?, ?, ?)
            ''', (payroll_id, deduction['deduction_id'], deduction['amount']))
        
        conn.commit()
        return jsonify({'payroll_id': payroll_id}), 201
    finally:
        conn.close()

@app.route('/api/payroll/<int:payroll_id>', methods=['DELETE'])
def delete_payroll(payroll_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM payroll WHERE payroll_id = ?", (payroll_id,))
    conn.commit()
    affected_rows = cursor.rowcount
    conn.close()
    
    if affected_rows > 0:
        return jsonify({"status": "success"}), 200
    else:
        return jsonify({"error": "Employee not found"}), 404

# DEDUCTION ENDPOINTS
@app.route('/api/deductions', methods=['GET', 'POST'])
def deductions():
    if request.method == 'GET':
        conn = get_db_connection()
        deductions = conn.execute('SELECT * FROM deduction').fetchall()
        conn.close()
        return jsonify([dict(row) for row in deductions])
    
    elif request.method == 'POST':
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO deduction (employee_id, deduction_type) VALUES (?, ?)',
            (data['employee_id'], data['deduction_type'])
        )
        conn.commit()
        conn.close()
        return jsonify({'deduction_id': cursor.lastrowid}), 201

# PAY RECORD ENDPOINTS
@app.route('/api/payrecords', methods=['POST'])
def add_pay_record():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        '''INSERT INTO pay_record 
        (employee_id, date_paid, amount, reference_number)
        VALUES (?, ?, ?, ?)''',
        (data['employee_id'], data['date_paid'], 
         data['amount'], data['reference_number'])
    )
    conn.commit()
    conn.close()
    return jsonify({'pay_id': cursor.lastrowid}), 201

def seed_default_users():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ADMIN (
            admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_super_admin INTEGER NOT NULL DEFAULT 0
        );
    ''')

    # Insert a default super admin if not exists
    cursor.execute('SELECT * FROM ADMIN WHERE username = ?', ('admin',))
    if cursor.fetchone() is None:
        cursor.execute(
            'INSERT INTO ADMIN (username, password, is_super_admin) VALUES (?, ?, ?)',
            ('admin', 'admin123', 1)
        )

    conn.commit()
    conn.close()

# Initialize and run the server
if __name__ == '__main__':
    seed_default_users()
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
