import sqlite3
from datetime import datetime


# CREATE
def create_connection(database_file):
    conn = sqlite3.connect(database_file)
    return conn


def create_table(conn, cursor):
    cursor.executescript('''
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
            time_in TIME NOT NULL,
            time_out TIME NOT NULL,
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

    conn.commit()


def add_employee(conn, cursor, lastname, firstname, daily_rate):
    cursor.execute('INSERT INTO employee (lastname, firstname, daily_rate) VALUES (?, ?, ?)', (lastname, firstname, daily_rate))
    conn.commit()
    print(f"Added employee: {lastname} at Php{daily_rate}")


def add_project(conn, cursor, project_name, project_start, project_end):
    cursor.execute('INSERT INTO project (project_name, project_start, project_end) VALUES (?, ?, ?)', (project_name, project_start, project_end))
    conn.commit()
    print(f"Added project {project_name}")

def compute_attendance_hours(time_in_str, time_out_str):
    time_format = "%H:%M"
    time_in = datetime.strptime(time_in_str, time_format)
    time_out = datetime.strptime(time_out_str, time_format)
    
    if time_out <= time_in:
        raise ValueError("Time out must be after time in for same-day shifts.")

    attendance_hours = (time_out - time_in).seconds / 3600  # convert seconds to hours
    return attendance_hours

def add_attendance_log(conn, cursor, employee_id, project_id, time_in, time_out, date):
    attendance_hours = compute_attendance_hours(time_in, time_out)

    if attendance_hours > 8:
        overtime_hours = attendance_hours - 8

    cursor.execute('''
                    INSERT INTO attendance_log
                        (employee_id, project_id, time_in, time_out. overtime_hours, date, attendance_hours)
                    VALUES
                        (?, ?, ?, ?, ?, ?, ?)''', (employee_id, project_id, time_in, time_in, overtime_hours, date, attendance_hours))
    conn.commit()
    print(f"Added attendance for {date}")

def add_deduction(conn, cursor, employee_id, deduction_type):
    cursor.execute('''
                   INSERT INTO deduction
                       (employee_id, deduction_type)
                   VALUES
                       (?, ?)
                   ''', (employee_id, deduction_type))
    conn.commit()
    print(f"Added deduction {deduction_type}")


def add_payroll(conn, cursor, gross_salary, net_salary,
                week_start, week_end, attendance_log_id):
    # This may be wrong
    cursor.execute('''
                   INSERT INTO payroll
                       (attendance_log_id, gross_salary, net_salary,
                        week_start, week_end)
                   VALUES
                       (?, ?, ?, ?, ?)
                   ''', (attendance_log_id, gross_salary, net_salary,
                         week_start, week_end))
    conn.commit()
    print("Added new payroll")


def add_pay_record(conn, cursor, date_paid, paid_amount,
                   employee_daily_rate, payroll_id):
    cursor.execute('''
                   INSERT INTO pay_record
                       (date_paid, paid_amount, employee_daily_rate,
                        payroll_id)
                   VALUES
                       (?, ?, ?, ?)
                   ''', (date_paid, paid_amount, employee_daily_rate,
                         payroll_id))
    conn.commit()


# READ
def read_employees(conn, cursor):
    cursor.execute('SELECT * FROM employees')
    return cursor.fetchall()


def main():
    database = "payroll_app.db"
    conn = create_connection(database)
    cursor = conn.cursor()
    
    if conn is None:
        print("Error: No connection")
        exit()

    create_table(conn, cursor)


if __name__ == '__main__':
    main()