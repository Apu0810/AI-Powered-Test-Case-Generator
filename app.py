"""
AI-Powered Software Requirements and Test Case Generator
Flask Application Main Controller & REST API
MCA Lab Practical Demonstration
"""
import os
import json
import csv
import io
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response

from database import init_db, get_db_connection
from validator import validate_student_registration
from ai_generator import generate_test_cases, get_prompt_template

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'mca-genai-lab-practical-secret-key-2026')

# Initialize SQLite database on startup
init_db(force_reset=False)


# ============================================================================
# PAGE ROUTES
# ============================================================================

@app.route('/')
def index():
    """Serves the main application dashboard and 4-section interface."""
    return render_template('index.html')


@app.route('/report/printable')
def printable_report():
    """Renders a comprehensive, printable 11-section formal testing report."""
    conn = get_db_connection()
    requirements = conn.execute("SELECT * FROM requirements ORDER BY id ASC").fetchall()
    test_cases = conn.execute("SELECT * FROM test_cases ORDER BY id ASC").fetchall()
    defects = conn.execute("SELECT * FROM defects ORDER BY id ASC").fetchall()
    students = conn.execute("SELECT * FROM students ORDER BY id ASC").fetchall()
    conn.close()

    # Calculate statistics
    total_tests = len(test_cases)
    passed_tests = sum(1 for tc in test_cases if tc['status'] == 'PASS')
    failed_tests = sum(1 for tc in test_cases if tc['status'] == 'FAIL')
    unexecuted_tests = sum(1 for tc in test_cases if tc['status'] == 'Not Executed')
    executed_tests = passed_tests + failed_tests
    pass_percentage = round((passed_tests / executed_tests * 100), 1) if executed_tests > 0 else 0

    return render_template(
        'report_printable.html',
        requirements=requirements,
        test_cases=test_cases,
        defects=defects,
        students=students,
        stats={
            "total_reqs": len(requirements),
            "total_tests": total_tests,
            "executed": executed_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "pending": unexecuted_tests,
            "pass_rate": pass_percentage,
            "total_defects": len(defects)
        },
        generated_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )


# ============================================================================
# SYSTEM UNDER TEST: STUDENT REGISTRATION API (FR1, FR2, FR3)
# ============================================================================

@app.route('/api/register', methods=['POST'])
def register_student():
    """
    FR1, FR2, FR3: Live Student Registration Endpoint.
    Validates input, checks duplicate email, hashes password, saves record.
    """
    payload = request.get_json(silent=True) or request.form.to_dict()
    if not payload:
        return jsonify({
            "status": "error",
            "message": "Malformed or empty JSON request body."
        }), 400

    # 1. Server-side validation
    is_valid, validation_errors = validate_student_registration(payload)
    if not is_valid:
        return jsonify({
            "status": "error",
            "message": "Validation failed.",
            "errors": validation_errors
        }), 400

    full_name = payload["full_name"].strip()
    email = payload["email"].strip().lower()
    raw_password = payload["password"]
    phone = payload["phone"].strip()
    course = payload["course"].strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    # 2. Duplicate email prevention (FR3)
    cursor.execute("SELECT id FROM students WHERE LOWER(email) = ?", (email,))
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return jsonify({
            "status": "error",
            "message": f"Duplicate Email Error: An account with email '{email}' already exists in the system."
        }), 409

    # 3. Secure password hashing
    from werkzeug.security import generate_password_hash
    password_hash = generate_password_hash(raw_password)

    # 4. Insert student record using parameterized query
    cursor.execute("""
        INSERT INTO students (full_name, email, password_hash, phone, course)
        VALUES (?, ?, ?, ?, ?)
    """, (full_name, email, password_hash, phone, course))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return jsonify({
        "status": "success",
        "message": "Registration successful! Student record created.",
        "student": {
            "id": new_id,
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "course": course
        }
    }), 201


@app.route('/api/students', methods=['GET'])
def get_students():
    """Returns all registered students for verification."""
    conn = get_db_connection()
    rows = conn.execute("SELECT id, full_name, email, password_hash, phone, course, registered_at FROM students ORDER BY id DESC").fetchall()
    conn.close()
    
    students = []
    for r in rows:
        students.append({
            "id": r["id"],
            "full_name": r["full_name"],
            "email": r["email"],
            "password_hash": r["password_hash"][:18] + "...",  # Truncated hash for safe display
            "phone": r["phone"],
            "course": r["course"],
            "registered_at": r["registered_at"]
        })
    return jsonify({"status": "success", "students": students})


# ============================================================================
# REQUIREMENTS API (FR4: Full CRUD Operations)
# ============================================================================

@app.route('/api/requirements', methods=['GET', 'POST'])
def handle_requirements():
    """Fetches all functional requirements with test case counts, or creates a new one."""
    conn = get_db_connection()

    if request.method == 'POST':
        data = request.get_json() or {}
        req_code = str(data.get("req_code", "")).strip().upper()
        title = str(data.get("title", "")).strip()
        description = str(data.get("description", "")).strip()
        category = str(data.get("category", "Functional")).strip()

        if not req_code or not title or not description:
            conn.close()
            return jsonify({"status": "error", "message": "Requirement ID, Title, and Description are required."}), 400

        # Check for duplicate requirement code
        existing = conn.execute("SELECT id FROM requirements WHERE req_code = ?", (req_code,)).fetchone()
        if existing:
            conn.close()
            return jsonify({"status": "error", "message": f"Requirement with code '{req_code}' already exists."}), 409

        try:
            conn.execute("""
                INSERT INTO requirements (req_code, title, description, category)
                VALUES (?, ?, ?, ?)
            """, (req_code, title, description, category))
            conn.commit()
            conn.close()
            return jsonify({"status": "success", "message": f"Requirement {req_code} saved successfully."}), 201
        except Exception as e:
            conn.close()
            return jsonify({"status": "error", "message": f"Failed to save requirement: {str(e)}"}), 400

    # GET: return list with count of linked test cases
    rows = conn.execute("""
        SELECT r.id, r.req_code, r.title, r.description, r.category, r.created_at,
               COUNT(tc.id) AS test_case_count
        FROM requirements r
        LEFT JOIN test_cases tc ON r.req_code = tc.req_code
        GROUP BY r.id
        ORDER BY r.id ASC
    """).fetchall()
    conn.close()
    return jsonify({"status": "success", "requirements": [dict(r) for r in rows]})


@app.route('/api/requirements/<req_code>', methods=['GET', 'PUT', 'DELETE'])
def single_requirement(req_code):
    """View, Edit, or Delete a specific requirement."""
    conn = get_db_connection()
    req_code = req_code.strip().upper()

    row = conn.execute("SELECT * FROM requirements WHERE req_code = ?", (req_code,)).fetchone()
    if not row:
        conn.close()
        return jsonify({"status": "error", "message": f"Requirement {req_code} not found."}), 404

    if request.method == 'GET':
        conn.close()
        return jsonify({"status": "success", "requirement": dict(row)})

    elif request.method == 'PUT':
        data = request.get_json() or {}
        title = str(data.get("title", row["title"])).strip()
        description = str(data.get("description", row["description"])).strip()
        category = str(data.get("category", row["category"])).strip()

        if not title or not description:
            conn.close()
            return jsonify({"status": "error", "message": "Title and description cannot be empty."}), 400

        conn.execute("""
            UPDATE requirements
            SET title = ?, description = ?, category = ?
            WHERE req_code = ?
        """, (title, description, category, req_code))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": f"Requirement {req_code} updated successfully."})

    elif request.method == 'DELETE':
        # Delete associated test cases and defects as well
        cursor = conn.cursor()
        cursor.execute("SELECT tc_id FROM test_cases WHERE req_code = ?", (req_code,))
        tc_ids = [r[0] for r in cursor.fetchall()]
        for tc_id in tc_ids:
            cursor.execute("DELETE FROM defects WHERE tc_id = ?", (tc_id,))
        cursor.execute("DELETE FROM test_cases WHERE req_code = ?", (req_code,))
        cursor.execute("DELETE FROM requirements WHERE req_code = ?", (req_code,))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": f"Requirement {req_code} and its linked test cases deleted."})


@app.route('/api/prompt-template', methods=['GET'])
def get_prompt():
    """Returns the actual Generative AI prompt for inspection (Mandatory Task C)."""
    req_code = request.args.get('req_code', 'FR1')
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM requirements WHERE req_code = ?", (req_code,)).fetchone()
    conn.close()

    title = row["title"] if row else "Student Registration"
    desc = row["description"] if row else "Registration portal specifications"

    prompt_text = get_prompt_template(req_code, title, desc)
    return jsonify({
        "status": "success",
        "req_code": req_code,
        "prompt": prompt_text
    })


# ============================================================================
# AI TEST CASE GENERATION API (FR5, FR6)
# ============================================================================

@app.route('/api/generate-test-cases', methods=['POST'])
def generate_tc_route():
    """
    Invokes Generative AI or transparent keyword-aware local fallback to generate
    at least eight structured test cases for a requirement. Saves them to database.
    """
    data = request.get_json() or {}
    req_code = str(data.get("req_code", "FR1")).strip().upper()
    force_fallback = data.get("force_fallback", False)

    conn = get_db_connection()
    row = conn.execute("SELECT * FROM requirements WHERE req_code = ?", (req_code,)).fetchone()
    if not row:
        conn.close()
        return jsonify({"status": "error", "message": f"Requirement '{req_code}' not found."}), 404

    gen_result = generate_test_cases(row["req_code"], row["title"], row["description"], force_fallback=force_fallback)
    test_cases = gen_result["test_cases"]

    # Save generated test cases into SQLite
    cursor = conn.cursor()
    saved_count = 0
    for tc in test_cases:
        tc_id = tc.get("tc_id")
        input_data = tc.get("input_data")
        if isinstance(input_data, dict):
            input_data = json.dumps(input_data)
        elif not isinstance(input_data, str):
            input_data = "{}"

        # Insert or replace
        cursor.execute("""
            INSERT INTO test_cases (tc_id, req_code, scenario, test_type, input_data, expected_result, actual_result, status, defect_desc)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(tc_id) DO UPDATE SET
                req_code = excluded.req_code,
                scenario = excluded.scenario,
                test_type = excluded.test_type,
                input_data = excluded.input_data,
                expected_result = excluded.expected_result,
                actual_result = '',
                status = 'Not Executed',
                defect_desc = ''
        """, (
            tc_id,
            tc.get("req_code", req_code),
            tc.get("scenario", "Generated Scenario"),
            tc.get("test_type", "Positive"),
            input_data,
            tc.get("expected_result", "Expected 200/201"),
            "",
            "Not Executed",
            ""
        ))
        saved_count += 1

    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "engine": gen_result["engine"],
        "prompt_used": gen_result["prompt_used"],
        "count": saved_count,
        "test_cases": test_cases
    })


# ============================================================================
# TEST CASES MANAGEMENT & EXECUTION (FR6, FR7, FR9)
# ============================================================================

@app.route('/api/test-cases', methods=['GET', 'POST'])
def handle_test_cases():
    """Retrieves all test cases with filters, or adds a new test case."""
    conn = get_db_connection()

    if request.method == 'POST':
        data = request.get_json() or {}
        tc_id = str(data.get("tc_id", "")).strip().upper()
        req_code = str(data.get("req_code", "")).strip().upper()
        scenario = str(data.get("scenario", "")).strip()
        test_type = str(data.get("test_type", "Positive")).strip()
        input_data = data.get("input_data", "{}")
        if isinstance(input_data, dict):
            input_data = json.dumps(input_data)
        expected_result = str(data.get("expected_result", "")).strip()

        if not tc_id or not req_code or not scenario or not expected_result:
            conn.close()
            return jsonify({"status": "error", "message": "Test Case ID, Req ID, Scenario, and Expected Result are required."}), 400

        try:
            conn.execute("""
                INSERT INTO test_cases (tc_id, req_code, scenario, test_type, input_data, expected_result, actual_result, status, defect_desc)
                VALUES (?, ?, ?, ?, ?, ?, '', 'Not Executed', '')
            """, (tc_id, req_code, scenario, test_type, input_data, expected_result))
            conn.commit()
            conn.close()
            return jsonify({"status": "success", "message": f"Test case {tc_id} created."}), 201
        except Exception as e:
            conn.close()
            return jsonify({"status": "error", "message": f"Failed to add test case: {str(e)}"}), 400

    # GET
    status_filter = request.args.get('status')
    req_filter = request.args.get('req_code')
    search = request.args.get('search', '').strip().lower()

    query = "SELECT * FROM test_cases WHERE 1=1"
    params = []
    if status_filter and status_filter != 'ALL':
        query += " AND status = ?"
        params.append(status_filter)
    if req_filter and req_filter != 'ALL':
        query += " AND req_code = ?"
        params.append(req_filter)
    if search:
        query += " AND (LOWER(tc_id) LIKE ? OR LOWER(scenario) LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    query += " ORDER BY id ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()

    return jsonify({
        "status": "success",
        "test_cases": [dict(r) for r in rows]
    })


@app.route('/api/test-cases/<tc_id>', methods=['PUT', 'DELETE'])
def single_test_case(tc_id):
    """Edit or Delete a test case."""
    conn = get_db_connection()
    tc = conn.execute("SELECT * FROM test_cases WHERE tc_id = ?", (tc_id,)).fetchone()
    if not tc:
        conn.close()
        return jsonify({"status": "error", "message": f"Test case {tc_id} not found."}), 404

    if request.method == 'PUT':
        data = request.get_json() or {}
        scenario = str(data.get("scenario", tc["scenario"])).strip()
        test_type = str(data.get("test_type", tc["test_type"])).strip()
        input_data = data.get("input_data", tc["input_data"])
        if isinstance(input_data, dict):
            input_data = json.dumps(input_data)
        expected_result = str(data.get("expected_result", tc["expected_result"])).strip()

        conn.execute("""
            UPDATE test_cases
            SET scenario = ?, test_type = ?, input_data = ?, expected_result = ?
            WHERE tc_id = ?
        """, (scenario, test_type, input_data, expected_result, tc_id))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": f"Test case {tc_id} updated."})

    elif request.method == 'DELETE':
        conn.execute("DELETE FROM defects WHERE tc_id = ?", (tc_id,))
        conn.execute("DELETE FROM test_cases WHERE tc_id = ?", (tc_id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": f"Test case {tc_id} deleted."})


def _evaluate_live_registration_test(tc_id, input_data, expected_result):
    """
    Core test execution logic for Student Registration Portal.
    Runs the actual server-side validation and database integrity checks.
    Compares the actual observed response against the expected result.
    Returns: (final_status, actual_result, defect_desc)
    """
    with app.test_client() as client:
        response = client.post('/api/register', json=input_data)
        status_code = response.status_code
        try:
            resp_json = response.get_json() or {}
        except Exception:
            resp_json = {}

    actual_msg = resp_json.get('message', '')
    errors = resp_json.get('errors', {})
    actual_result = f"HTTP {status_code}: {actual_msg}"
    if errors:
        actual_result += f" (Fields: {', '.join(errors.keys())})"

    # STRICT COMPARISON:
    # PASS only if observed HTTP code or outcome aligns with expectation.
    expected_lower = expected_result.lower()
    is_match = False

    if str(status_code) in expected_result or f"http {status_code}" in expected_lower:
        is_match = True
    elif "201" in expected_result and status_code == 201:
        is_match = True
    elif "400" in expected_result and status_code == 400:
        is_match = True
    elif "409" in expected_result and status_code == 409:
        is_match = True

    final_status = "PASS" if is_match else "FAIL"
    defect_desc = ""
    if final_status == "FAIL":
        defect_desc = f"Mismatch: Observed '{actual_result}', but expected '{expected_result}'."

    return final_status, actual_result, defect_desc


@app.route('/api/test-cases/execute-live/<tc_id>', methods=['POST'])
def execute_test_live(tc_id):
    """
    Executes a test case against the live Student Registration Portal API in real time.
    Truthfully records actual response, compares against expected result, and determines PASS/FAIL.
    """
    conn = get_db_connection()
    tc = conn.execute("SELECT * FROM test_cases WHERE tc_id = ?", (tc_id,)).fetchone()
    if not tc:
        conn.close()
        return jsonify({"status": "error", "message": f"Test case {tc_id} not found."}), 404

    # Parse input data
    try:
        input_data = json.loads(tc["input_data"])
    except Exception:
        input_data = {}

    expected_result = tc["expected_result"]

    # Check if test case contains registration fields suitable for automated execution
    is_automated_target = isinstance(input_data, dict) and any(
        k in input_data for k in ["full_name", "email", "password", "phone", "course"]
    )

    if not is_automated_target:
        conn.close()
        return jsonify({
            "status": "error",
            "message": "This test case does not target the automated registration endpoint. Please use Manual Execution to record your observation.",
            "manual_required": True
        }), 400

    final_status, actual_result, defect_desc = _evaluate_live_registration_test(tc_id, input_data, expected_result)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE test_cases
        SET actual_result = ?, status = ?, defect_desc = ?, executed_at = ?
        WHERE tc_id = ?
    """, (actual_result, final_status, defect_desc, now, tc_id))

    # Real Defect Logging: Record actual defect only when failure observed
    if final_status == "FAIL":
        cursor.execute("SELECT id FROM defects WHERE tc_id = ?", (tc_id,))
        existing = cursor.fetchone()
        if existing:
            cursor.execute("""
                UPDATE defects
                SET description = ?, expected_result = ?, actual_result = ?, status = 'Open'
                WHERE tc_id = ?
            """, (defect_desc, expected_result, actual_result, tc_id))
        else:
            cursor.execute("""
                INSERT INTO defects (tc_id, description, expected_result, actual_result, severity, status)
                VALUES (?, ?, ?, ?, 'High', 'Open')
            """, (tc_id, defect_desc, expected_result, actual_result))
    else:
        # If test passes, resolve/close any prior defect for this test case
        cursor.execute("UPDATE defects SET status = 'Resolved' WHERE tc_id = ?", (tc_id,))

    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "tc_id": tc_id,
        "test_status": final_status,
        "actual_result": actual_result,
        "expected_result": expected_result,
        "defect_desc": defect_desc
    })


@app.route('/api/test-cases/execute-manual', methods=['POST'])
def execute_test_manual():
    """
    FR7, FR9: Records manual test execution result.
    Compares expected with actual and updates status to PASS or FAIL.
    """
    data = request.get_json() or {}
    tc_id = data.get("tc_id")
    actual_result = str(data.get("actual_result", "")).strip()
    status = str(data.get("status", "Not Executed")).strip()
    defect_desc = str(data.get("defect_desc", "")).strip()

    if not tc_id or status not in ["Not Executed", "PASS", "FAIL"]:
        return jsonify({"status": "error", "message": "Valid tc_id and status (Not Executed, PASS, FAIL) are required."}), 400

    conn = get_db_connection()
    tc = conn.execute("SELECT expected_result FROM test_cases WHERE tc_id = ?", (tc_id,)).fetchone()
    if not tc:
        conn.close()
        return jsonify({"status": "error", "message": f"Test case {tc_id} not found."}), 404

    expected_result = tc["expected_result"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE test_cases
        SET actual_result = ?, status = ?, defect_desc = ?, executed_at = ?
        WHERE tc_id = ?
    """, (actual_result, status, defect_desc, now, tc_id))

    # Defect tracking (FR9)
    if status == 'FAIL':
        desc = defect_desc or f"Manual failure recorded: Actual observed result '{actual_result}' does not match expected."
        cursor.execute("SELECT id FROM defects WHERE tc_id = ?", (tc_id,))
        existing_defect = cursor.fetchone()
        if existing_defect:
            cursor.execute("""
                UPDATE defects
                SET description = ?, expected_result = ?, actual_result = ?, status = 'Open'
                WHERE tc_id = ?
            """, (desc, expected_result, actual_result, tc_id))
        else:
            cursor.execute("""
                INSERT INTO defects (tc_id, description, expected_result, actual_result, severity, status)
                VALUES (?, ?, ?, ?, 'High', 'Open')
            """, (tc_id, desc, expected_result, actual_result))
    elif status == 'PASS':
        cursor.execute("UPDATE defects SET status = 'Resolved' WHERE tc_id = ?", (tc_id,))

    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": f"Test case {tc_id} execution updated."})


@app.route('/api/test-cases/execute-all-live', methods=['POST'])
def execute_all_live():
    """
    Runs all supported automated test cases against the live portal API.
    Manual-only test cases remain 'Not Executed' until an actual result is recorded.
    """
    conn = get_db_connection()
    test_cases = conn.execute("SELECT tc_id, input_data FROM test_cases ORDER BY id ASC").fetchall()
    conn.close()

    executed_count = 0
    passed_count = 0
    failed_count = 0
    manual_count = 0

    results = []
    for row in test_cases:
        tc_id = row["tc_id"]
        try:
            inp = json.loads(row["input_data"])
        except Exception:
            inp = {}

        # Only execute automated registration tests; leave manual-only tests as Not Executed
        if isinstance(inp, dict) and any(k in inp for k in ["full_name", "email", "password", "phone", "course"]):
            res = execute_test_live(tc_id)
            res_data = res.get_json()
            executed_count += 1
            if res_data.get("test_status") == "PASS":
                passed_count += 1
            else:
                failed_count += 1
            results.append(res_data)
        else:
            manual_count += 1

    return jsonify({
        "status": "success",
        "message": f"Executed {executed_count} automated test cases. {passed_count} passed, {failed_count} failed. {manual_count} manual test cases left as Not Executed.",
        "executed_count": executed_count,
        "passed_count": passed_count,
        "failed_count": failed_count,
        "manual_count": manual_count,
        "results": results
    })


# ============================================================================
# DEFECTS API (FR9)
# ============================================================================

@app.route('/api/defects', methods=['GET', 'POST'])
def handle_defects():
    """Lists all defects or creates a new defect entry."""
    conn = get_db_connection()

    if request.method == 'POST':
        data = request.get_json() or {}
        tc_id = str(data.get("tc_id", "")).strip().upper()
        desc = str(data.get("description", "")).strip()
        expected = str(data.get("expected_result", "")).strip()
        actual = str(data.get("actual_result", "")).strip()
        severity = str(data.get("severity", "High")).strip()
        status = str(data.get("status", "Open")).strip()

        if not tc_id or not desc:
            conn.close()
            return jsonify({"status": "error", "message": "Test Case ID and Description are required."}), 400

        conn.execute("""
            INSERT INTO defects (tc_id, description, expected_result, actual_result, severity, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (tc_id, desc, expected, actual, severity, status))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Defect logged successfully."}), 201

    rows = conn.execute("SELECT * FROM defects ORDER BY id DESC").fetchall()
    conn.close()
    return jsonify({"status": "success", "defects": [dict(r) for r in rows]})


@app.route('/api/defects/<int:defect_id>', methods=['PUT', 'DELETE'])
def single_defect(defect_id):
    """Updates defect status (Open, In Progress, Resolved, Closed) or deletes defect."""
    conn = get_db_connection()
    defect = conn.execute("SELECT * FROM defects WHERE id = ?", (defect_id,)).fetchone()
    if not defect:
        conn.close()
        return jsonify({"status": "error", "message": f"Defect #{defect_id} not found."}), 404

    if request.method == 'PUT':
        data = request.get_json() or {}
        new_status = data.get("status", defect["status"])
        new_severity = data.get("severity", defect["severity"])
        new_desc = data.get("description", defect["description"])

        conn.execute("""
            UPDATE defects
            SET status = ?, severity = ?, description = ?
            WHERE id = ?
        """, (new_status, new_severity, new_desc, defect_id))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": f"Defect #{defect_id} updated."})

    elif request.method == 'DELETE':
        conn.execute("DELETE FROM defects WHERE id = ?", (defect_id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": f"Defect #{defect_id} deleted."})


# ============================================================================
# REPORTING & EXPORT (FR8, FR10)
# ============================================================================

@app.route('/api/report/summary', methods=['GET'])
def get_report_summary():
    """Returns actual real-time dashboard metrics from the SQLite database."""
    conn = get_db_connection()
    req_count = conn.execute("SELECT COUNT(*) FROM requirements").fetchone()[0]
    tc_rows = conn.execute("SELECT status FROM test_cases").fetchall()
    open_defect_count = conn.execute("SELECT COUNT(*) FROM defects WHERE status = 'Open'").fetchone()[0]
    total_defects = conn.execute("SELECT COUNT(*) FROM defects").fetchone()[0]
    student_count = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    conn.close()

    total_tests = len(tc_rows)
    passed = sum(1 for r in tc_rows if r["status"] == "PASS")
    failed = sum(1 for r in tc_rows if r["status"] == "FAIL")
    pending = sum(1 for r in tc_rows if r["status"] == "Not Executed")
    executed = passed + failed
    pass_rate = round((passed / executed * 100), 1) if executed > 0 else 0

    return jsonify({
        "status": "success",
        "summary": {
            "total_requirements": req_count,
            "total_test_cases": total_tests,
            "tests_executed": executed,
            "passed": passed,
            "failed": failed,
            "pending": pending,
            "pass_rate": pass_rate,
            "open_defects": open_defect_count,
            "total_defects": total_defects,
            "registered_students": student_count
        }
    })


@app.route('/api/report/export-csv', methods=['GET'])
def export_csv():
    """FR10: Exports the full test execution report as a downloadable CSV file."""
    conn = get_db_connection()
    test_cases = conn.execute("""
        SELECT tc.tc_id, tc.req_code, r.title AS req_title, tc.scenario,
               tc.test_type, tc.input_data, tc.expected_result, tc.actual_result,
               tc.status, tc.defect_desc, tc.executed_at
        FROM test_cases tc
        LEFT JOIN requirements r ON tc.req_code = r.req_code
        ORDER BY tc.id ASC
    """).fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Test Case ID",
        "Requirement ID",
        "Requirement Title",
        "Test Scenario",
        "Test Type",
        "Input Data",
        "Expected Result",
        "Actual Result",
        "Status",
        "Defect Description",
        "Executed At"
    ])

    for row in test_cases:
        writer.writerow([
            row["tc_id"],
            row["req_code"],
            row["req_title"] or "",
            row["scenario"],
            row["test_type"],
            row["input_data"],
            row["expected_result"],
            row["actual_result"],
            row["status"],
            row["defect_desc"],
            row["executed_at"] or "N/A"
        ])

    csv_data = output.getvalue()
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=Student_Portal_Testing_Report.csv"}
    )


@app.route('/api/reset-data', methods=['POST'])
def reset_data():
    """Resets the database to clean baseline demo state with FR1-FR10 and core test cases."""
    init_db(force_reset=True)
    return jsonify({
        "status": "success",
        "message": "Database reset successfully to clean initial state."
    })


# ============================================================================
# APPLICATION ENTRYPOINT
# ============================================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"[*] Starting AI Test Case Generator on http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
