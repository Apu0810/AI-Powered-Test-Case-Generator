"""
Database Management Module for AI-Powered Test Case Generator
Handles SQLite connection, schema definition, parameterized queries, and seed data.
"""
import sqlite3
import os
import json
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")


def get_db_connection():
    """Returns a connection to the SQLite database with dictionary-like row access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(force_reset=False):
    """
    Initializes database tables and populates baseline requirements and seed test cases.
    If force_reset is True, existing tables are dropped and re-initialized.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    if force_reset:
        cursor.execute("DROP TABLE IF EXISTS defects")
        cursor.execute("DROP TABLE IF EXISTS test_cases")
        cursor.execute("DROP TABLE IF EXISTS requirements")
        cursor.execute("DROP TABLE IF EXISTS students")

    # 1. Requirements Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS requirements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            req_code TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT DEFAULT 'Functional',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. Test Cases Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tc_id TEXT UNIQUE NOT NULL,
            req_code TEXT NOT NULL,
            scenario TEXT NOT NULL,
            test_type TEXT DEFAULT 'Positive',
            input_data TEXT NOT NULL,
            expected_result TEXT NOT NULL,
            actual_result TEXT DEFAULT '',
            status TEXT DEFAULT 'Not Executed',
            defect_desc TEXT DEFAULT '',
            executed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (req_code) REFERENCES requirements(req_code)
        )
    """)

    # 3. Students Table (System Under Test)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            phone TEXT NOT NULL,
            course TEXT NOT NULL,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 4. Defects Table (Includes Expected and Actual Results for Defect Traceability)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS defects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tc_id TEXT NOT NULL,
            description TEXT NOT NULL,
            expected_result TEXT DEFAULT '',
            actual_result TEXT DEFAULT '',
            severity TEXT DEFAULT 'High',
            status TEXT DEFAULT 'Open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tc_id) REFERENCES test_cases(tc_id)
        )
    """)

    # Ensure backward compatibility for existing databases
    cursor.execute("PRAGMA table_info(defects)")
    defect_cols = [col[1] for col in cursor.fetchall()]
    if "expected_result" not in defect_cols:
        cursor.execute("ALTER TABLE defects ADD COLUMN expected_result TEXT DEFAULT ''")
    if "actual_result" not in defect_cols:
        cursor.execute("ALTER TABLE defects ADD COLUMN actual_result TEXT DEFAULT ''")

    conn.commit()

    # Seed baseline requirements if not present
    cursor.execute("SELECT COUNT(*) FROM requirements")
    if cursor.fetchone()[0] == 0:
        seed_requirements(cursor)

    # Seed baseline test cases if not present
    cursor.execute("SELECT COUNT(*) FROM test_cases")
    if cursor.fetchone()[0] == 0:
        seed_test_cases(cursor)

    # Seed an existing student record for duplicate email testing
    cursor.execute("SELECT COUNT(*) FROM students")
    if cursor.fetchone()[0] == 0:
        demo_hashed = generate_password_hash("Password123")
        cursor.execute("""
            INSERT INTO students (full_name, email, password_hash, phone, course)
            VALUES (?, ?, ?, ?, ?)
        """, ("Arun Kumar", "arun.kumar@example.com", demo_hashed, "9876543210", "MCA"))

    conn.commit()
    conn.close()


def seed_requirements(cursor):
    """Inserts the 10 official Functional Requirements into the database."""
    default_requirements = [
        ("FR1", "Student Registration", "The system should allow students to register using their full name, email, password, phone number, and course.", "Functional"),
        ("FR2", "Input Validation", "The system should validate required fields, email format, password length (min 8 chars, alphanumeric), and phone number format (10 digits).", "Functional"),
        ("FR3", "Duplicate Email Prevention", "The system should prevent registration using an email address that is already registered in the system.", "Security & Integrity"),
        ("FR4", "Requirement Entry", "The user should be able to enter a software requirement or select predefined requirements.", "System Feature"),
        ("FR5", "AI-Assisted Test Case Generation", "The system should convert entered requirements into structured test cases using a well-designed Generative AI prompt. Provide a fallback generator if no AI API is configured.", "Generative AI"),
        ("FR6", "Test Case Management", "The user should be able to view generated test cases in a table and include at least eight test cases covering positive scenarios, negative scenarios, invalid inputs, and boundary conditions.", "Test Management"),
        ("FR7", "Manual Test Execution", "The user should be able to enter or record the actual result of a test case, compare it with the expected result, and mark it PASS or FAIL.", "Test Execution"),
        ("FR8", "Test Report", "The system should generate a testing report containing requirements, test cases, input data, expected results, actual results, execution status, defects, and a final summary.", "Reporting"),
        ("FR9", "Defect Tracking", "When a test case fails, record a defect description and its status. Do not invent defects when no failure has been observed.", "Defect Management"),
        ("FR10", "Export", "Allow the user to download the final testing report as a CSV file or a printable HTML report.", "Export & Integration")
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO requirements (req_code, title, description, category)
        VALUES (?, ?, ?, ?)
    """, default_requirements)


def seed_test_cases(cursor):
    """
    Inserts at least 8 structured test cases meeting Task D requirements:
    - Valid registration details
    - Empty required fields
    - Invalid email format
    - Duplicate email
    - Invalid or too-short password
    - Invalid phone number
    - Minimum valid input boundary
    - Maximum allowed input length or exceeding limit
    """
    core_test_cases = [
        (
            "TC-REG-01",
            "FR1",
            "Verify successful student registration with all valid details",
            "Positive",
            json.dumps({
                "full_name": "Priya Sharma",
                "email": "priya.sharma@example.com",
                "password": "SecurePass123",
                "phone": "9812345678",
                "course": "MCA"
            }),
            "HTTP 201 Created: Registration successful. Student record stored with hashed password.",
            "",
            "Not Executed",
            ""
        ),
        (
            "TC-REG-02",
            "FR2",
            "Verify error when mandatory fields are submitted empty",
            "Negative",
            json.dumps({
                "full_name": "",
                "email": "",
                "password": "",
                "phone": "",
                "course": ""
            }),
            "HTTP 400 Bad Request: Validation errors returned for all required fields.",
            "",
            "Not Executed",
            ""
        ),
        (
            "TC-REG-03",
            "FR2",
            "Verify registration rejection when email address has invalid format",
            "Negative",
            json.dumps({
                "full_name": "Rohan Verma",
                "email": "rohan_invalid_email.com",
                "password": "ValidPassword1",
                "phone": "9123456780",
                "course": "MCA"
            }),
            "HTTP 400 Bad Request: 'Invalid email format. Expected format: user@domain.com.'",
            "",
            "Not Executed",
            ""
        ),
        (
            "TC-REG-04",
            "FR3",
            "Verify registration fails when email is already registered (Duplicate check)",
            "Negative",
            json.dumps({
                "full_name": "Duplicate User",
                "email": "arun.kumar@example.com",
                "password": "Password123",
                "phone": "9876543211",
                "course": "M.Tech"
            }),
            "HTTP 409 Conflict: 'An account with this email address already exists.'",
            "",
            "Not Executed",
            ""
        ),
        (
            "TC-REG-05",
            "FR2",
            "Verify registration rejection when password is shorter than minimum 8 characters",
            "Negative",
            json.dumps({
                "full_name": "Amit Patel",
                "email": "amit.patel@example.com",
                "password": "Pass1",
                "phone": "9823456789",
                "course": "MCA"
            }),
            "HTTP 400 Bad Request: 'Password must be at least 8 characters long.'",
            "",
            "Not Executed",
            ""
        ),
        (
            "TC-REG-06",
            "FR2",
            "Verify registration rejection when phone number does not contain exactly 10 digits",
            "Negative",
            json.dumps({
                "full_name": "Kavita Rao",
                "email": "kavita.rao@example.com",
                "password": "SafePass2026",
                "phone": "98765ABC",
                "course": "MBA"
            }),
            "HTTP 400 Bad Request: 'Phone number must be exactly 10 numeric digits.'",
            "",
            "Not Executed",
            ""
        ),
        (
            "TC-REG-07",
            "FR2",
            "Verify registration boundary condition with minimum valid inputs (Name=2 chars, Password=8 chars)",
            "Boundary",
            json.dumps({
                "full_name": "Al",
                "email": "al@domain.com",
                "password": "Abc12345",
                "phone": "9000000001",
                "course": "MCA"
            }),
            "HTTP 201 Created: Registration successful for boundary minimum valid inputs.",
            "",
            "Not Executed",
            ""
        ),
        (
            "TC-REG-08",
            "FR2",
            "Verify registration boundary violation when full name exceeds 50 characters",
            "Boundary",
            json.dumps({
                "full_name": "Christopher Bartholomew Montgomery Alexander The Great Explorer",
                "email": "chris.explorer@example.com",
                "password": "BoundaryPass1",
                "phone": "9998887776",
                "course": "B.Tech"
            }),
            "HTTP 400 Bad Request: 'Full name cannot exceed 50 characters.'",
            "",
            "Not Executed",
            ""
        )
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO test_cases (
            tc_id, req_code, scenario, test_type, input_data,
            expected_result, actual_result, status, defect_desc
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, core_test_cases)
