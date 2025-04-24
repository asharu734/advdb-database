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

    CREATE TABLE IF NOT EXISTS PAYROLL_DEDUCTION
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

#CREATE
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

    overtime_hours = attendance_hours - 8 if attendance_hours > 8 else 0

    cursor.execute('''
                    INSERT INTO attendance_log
                        (employee_id, project_id, time_in, time_out, overtime_hours, date, attendance_hours)
                    VALUES
                        (?, ?, ?, ?, ?, ?, ?)
                ''', (employee_id, project_id, time_in, time_out, overtime_hours, date, attendance_hours))

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

def add_payroll_deduction(conn, cursor, payroll_id, deduction_id, deduction_amount):
    cursor.execute('''
                   INSERT INTO payroll_deduction
                       (payroll_id, deduction_id, deduction_amount)
                   VALUES
                       (?, ?, ?)
                   ''', (payroll_id, deduction_id, deduction_amount))
    conn.commit()
    print(f"Added deduction {deduction_id}")


def add_pay_record(conn, cursor, payroll_id, date_paid, amount):
    cursor.execute('''
                   INSERT INTO pay_record
                       (payroll_id, date_paid, amount)
                   VALUES
                       (?, ?, ?)
                   ''', (payroll_id, date_paid, amount))
    conn.commit()


# READ
def read_employees(cursor):
    cursor.execute('SELECT * FROM employee')
    return cursor.fetchall()


# UPDATE
def update_employees(conn, cursor, employee_id, lastname, 
                     firstname, daily_rate):
    cursor.execute('''
                   UPDATE employee SET
                   lastname = ?, firstname = ?, daily_rate = ?

                   WHERE
                   employee_id = ?
                   ''', (lastname, firstname, daily_rate, employee_id))
    conn.commit()

def update_project(conn, cursor,  project_name, project_start, project_end):
    cursor.execute('''
                   UPDATE project SET
                   project_name = ?, project_start = ?, project_end = ?

                   WHERE
                   project = ?
                   ''', (project_name, project_start, project_end))
    conn.commit()

def update_attendance_log(conn, cursor,  employee_id, project_id,
                     time_in, time_out, date):
    cursor.execute('''
                   UPDATE attendance_log SET
                   employee_id = ?, project_id = ?, time_in = ?, time_out = ?

                   WHERE
                   attendance_log = ?
                   ''', (employee_id, project_id, time_in, time_out, date))
    conn.commit()

def update_deduction(conn, cursor,  employee_id, deduction_type):
    cursor.execute('''
                   UPDATE deduction SET
                   employee_id = ?, deduction_type = ?

                   WHERE
                   deduction = ?
                   ''', (employee_id, deduction_type))
    conn.commit()

def update_payroll(conn, cursor,  gross_salary, net_salary,
                     week_start, week_end, attendance_log_id):
    #Since Harold isn't sure if this is correct, this also applies here.
    cursor.execute('''
                   UPDATE payroll SET
                   gross_salary = ?, net_salary = ?, week_start = ?, week_end = ?, attendance_log_id = ?

                   WHERE
                   payroll = ?
                   ''', (gross_salary, net_salary, week_start, week_end, attendance_log_id))
    conn.commit()

def update_payroll_deduction(conn, cursor,  payroll_id, deduction_id, deduction_amount):
    cursor.execute('''
                   UPDATE payroll_deduction SET
                   payroll_id = ?, deduction_id = ?, deduction_amount = ?

                   WHERE
                   payroll_deduction = ?
                   ''', (payroll_id, deduction_id, deduction_amount))
    conn.commit()

def update_pay_record(conn, cursor,  payroll_id, date_paid, amount):
    cursor.execute('''
                   UPDATE pay_record SET
                   payroll_id = ?, date_paid = ?, amount = ?

                   WHERE
                   pay_record = ?
                   ''', (payroll_id, date_paid, amount))
    conn.commit()

# DELETE
def delete_employee(conn, cursor, employee_id):
    cursor.execute('DELETE FROM employee WHERE employee_id = ?', (employee_id,))
    conn.commit()


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