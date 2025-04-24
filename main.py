import sqlite3
from datetime import datetime

#Connect to the sqlite database
conn = sqlite3.connect("payroll_app.db")
crsr = conn.cursor()

conn.commit()

#FUNCTIONS

def create_table():
    crsr.executescript('''
    CREATE TABLE IF NOT EXISTS EMPLOYEE 
        (
            employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
            lastname TEXT NOT NULL,
            firstname TEXT NOT NULL,
            daily_rate REAL NOT NULL
        );

    CREATE TABLE IF NOT EXISTS PROJECT
        (
            project_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT NOT NULL,
            project_start DATE NOT NULL,
            project_end DATE
        );

    CREATE TABLE IF NOT EXISTS ATTENDANCE_LOG
        (
            attendance_log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            project_id INTEGER NOT NULL,
            time_in DATETIME NOT NULL,
            time_out DATETIME NOT NULL,
            overtime_hours REAL DEFAULT 0,
            date DATE NOT NULL,
            attendance_hours REAL,
            FOREIGN KEY (employee_id) REFERENCES EMPLOYEE(employee_id),
            FOREIGN KEY (project_id) REFERENCES PROJECT(project_id)
        );

    CREATE TABLE IF NOT EXISTS DEDUCTION
        (
            deduction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            deduction_type TEXT NOT NULL,
            FOREIGN KEY (employee_id) REFERENCES EMPLOYEE(employee_id)
        );

    CREATE TABLE IF NOT EXISTS PAYROLL
        (
            payroll_id INTEGER PRIMARY KEY AUTOINCREMENT,
            attendance_log_id INTEGER NOT NULL,
            gross_salary REAL NOT NULL,
            net_salary REAL NOT NULL,
            week_start DATE NOT NULL,
            week_end DATE NOT NULL,
            FOREIGN KEY (attendance_log_id) REFERENCES ATTENDANCE_LOG(attendance_log_id)
        );

    CREATE TABLE IF NOT EXISTS PAYROLL_DEDUTION
        (
            payroll_id INTEGER NOT NULL,
            deduction_id INTEGER NOT NULL,
            deduction_amount REAL NOT NULL,
            PRIMARY KEY(payroll_id, deduction_id),
            FOREIGN KEY (payroll_id) REFERENCES PAYROLL(payroll_id),
            FOREIGN KEY (deduction_id) REFERENCES DEDUCTION(deduction_id)
        );
                
    CREATE TABLE IF NOT EXISTS PAY_RECORD
        (
            pay_id INTEGER PRIMARY KEY AUTOINCREMENT,
            payroll_id INTEGER NOT NULL,
            date_paid DATE NOT NULL,
            amount REAL NOT NULL,
            FOREIGN KEY (payroll_id) REFERENCES PAYROLL(payroll_id)
        );

    ''')


def add_employee(lastname, firstname, daily_rate):
    crsr.execute('INSERT INTO employee (lastname, firstname, daily_rate) VALUES (?, ?, ?)', (lastname, firstname, daily_rate))
    conn.commit()
    print(f"Added employee: {lastname} at Php{daily_rate}")


def add_project(project_name, project_start, project_end):
    crsr.execute('INSERT INTO project (project_name, project_start, project_end) VALUES (?, ?, ?)', (project_name, project_start, project_end))
    conn.commit()
    print(f"Added project {project_name}")

def add_deduction(employee_id, deduction_type):
    crsr.execute("INSERT INTO employee_id, deduction_type", (employee_id, deduction_type))
    conn.commit()
    print(f"Deduction type has been added for {employee_id}")

def main():
    pass


if __name__ == '__main__':
    main()