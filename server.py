from functools import wraps
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os
import bcrypt
from database import create_connection, create_table
from utils import get_db_connection, hash_password, check_password
from auth.auth_routes import auth_bp
from datetime import datetime
import hmac
import hashlib
import base64
import json
import time

app = Flask(__name__)
app.register_blueprint(auth_bp, url_prefix="/auth")
CORS(app)

# Token settings
SECRET_KEY = b'your_super_secret_key_here'  # Replace with a strong key

def generate_token(user_id, role, expiry_seconds=3600):
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': int(time.time()) + expiry_seconds
    }
    payload_bytes = json.dumps(payload).encode()
    signature = hmac.new(SECRET_KEY, payload_bytes, hashlib.sha256).digest()
    
    token = base64.urlsafe_b64encode(payload_bytes + b'.' + signature).decode()
    return token

def decode_token(token):
    try:
        decoded = base64.urlsafe_b64decode(token.encode())
        payload_bytes, signature = decoded.rsplit(b'.', 1)
        
        expected_signature = hmac.new(SECRET_KEY, payload_bytes, hashlib.sha256).digest()
        if not hmac.compare_digest(signature, expected_signature):
            return None
        
        payload = json.loads(payload_bytes.decode())
        if payload['exp'] < int(time.time()):
            return None
        return payload
    except Exception:
        return None
        
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def require_role(allowed_roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith("Bearer "):
                return jsonify({'error': 'Missing or invalid token'}), 401
            token = auth_header.split(" ")[1]
            user_data = decode_token(token)
            if not user_data or user_data['role'] not in allowed_roles:
                return jsonify({'error': 'Unauthorized'}), 403
            request.user = user_data  # You can access it in views
            return f(*args, **kwargs)
        return wrapper
    return decorator


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
    CREATE TABLE IF NOT EXISTS USER (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('super_admin', 'admin'))
    );                     
    
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

# User management endpoints (super_admin only)
@app.route('/api/users', methods=['GET', 'POST'])
@require_role(['super_admin'])
def manage_users():
    if request.method == 'GET':
        conn = get_db_connection()
        users = conn.execute('SELECT user_id, username, role FROM user').fetchall()
        conn.close()
        return jsonify([dict(row) for row in users])
    
    elif request.method == 'POST':
        data = request.json
        if data['role'] not in ['super_admin', 'admin']:
            return jsonify({'error': 'Invalid role'}), 400
            
        hashed_pw = hash_password(data['password'])
        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO user (username, password, role) VALUES (?, ?, ?)',
                (data['username'], hashed_pw, data['role'])
            )
            conn.commit()
            return jsonify({'status': 'user created'}), 201
        except sqlite3.IntegrityError:
            return jsonify({'error': 'Username already exists'}), 400
        finally:
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
@require_role(['super_admin', 'admin'])
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
@require_role(['super_admin'])
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
@require_role(['super_admin', 'admin'])
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
@require_role(['super_admin'])
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
@require_role(['super_admin', 'admin'])
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
@require_role(['super_admin', 'admin'])
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

# PAYROLL ENDPOINTS
@app.route('/api/payroll', methods=['POST'])
@require_role(['super_admin', 'admin'])
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
@require_role(['super_admin'])
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
@require_role(['super_admin', 'admin'])
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
@require_role(['super_admin', 'admin'])
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

# Registration and Login Endpoints
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    hashed_pw = hash_password(data['password'])
    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT INTO user (username, password, role) VALUES (?, ?, ?)',
            (data['username'], hashed_pw, data['role'])
        )
        conn.commit()
        return jsonify({'status': 'registered'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username already exists'}), 400
    finally:
        conn.close()

@app.route('/api/login', methods=['POST'])
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM user WHERE username = ?', (data['username'],)).fetchone()
    conn.close()
    
    if user and check_password(data['password'], user['password']):
        token = generate_token(user['user_id'], user['role'])
        return jsonify({
            'status': 'success',
            'token': token,
            'user_id': user['user_id'],
            'role': user['role']
        }), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401



# Initialize and run the server
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
