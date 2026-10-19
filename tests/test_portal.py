"""
Automated Software Testing Suite for AI-Powered Test Case Generator
Target System: Student Registration Portal (FR1 - FR10)
Compatible with Python unittest and pytest.
"""
import unittest
import json
import os
import sys

# Ensure application modules can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app
from database import init_db, get_db_connection
from ai_generator import generate_test_cases, get_prompt_template
from validator import validate_student_registration


class TestStudentRegistrationAndAIGenerator(unittest.TestCase):
    """Automated test cases fulfilling Mandatory Task E and full application testing."""

    @classmethod
    def setUpClass(cls):
        """Configure test client and initialize baseline database once."""
        app.config['TESTING'] = True
        cls.client = app.test_client()

    def setUp(self):
        """Reset database to fresh baseline state before each test."""
        init_db(force_reset=True)

    # ------------------------------------------------------------------------
    # TASK E - EXECUTABLE TEST CASE 1: Valid registration data (Positive)
    # ------------------------------------------------------------------------
    def test_tc01_valid_registration(self):
        """Verify successful registration with valid student data."""
        payload = {
            "full_name": "Meera Krishnan",
            "email": "meera.krishnan@example.com",
            "password": "SecurePassword123",
            "phone": "9876543210",
            "course": "MCA"
        }

        response = self.client.post(
            '/api/register',
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("student", data)
        self.assertEqual(data["student"]["email"], "meera.krishnan@example.com")

        # Database Verification & Password Hash Security Check
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM students WHERE email = ?", ("meera.krishnan@example.com",)).fetchone()
        conn.close()

        self.assertIsNotNone(user)
        self.assertEqual(user["full_name"], "Meera Krishnan")
        # Ensure password is NOT stored as plaintext
        self.assertNotEqual(user["password_hash"], "SecurePassword123")
        self.assertTrue(user["password_hash"].startswith("pbkdf2:") or user["password_hash"].startswith("scrypt:"))

    # ------------------------------------------------------------------------
    # TASK E - EXECUTABLE TEST CASE 2: Missing required field or invalid email (Negative)
    # ------------------------------------------------------------------------
    def test_tc02_missing_required_fields(self):
        """Verify rejection when required fields are submitted empty."""
        payload = {
            "full_name": "",
            "email": "",
            "password": "",
            "phone": "",
            "course": ""
        }

        response = self.client.post(
            '/api/register',
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data["status"], "error")
        errors = data["errors"]
        self.assertIn("full_name", errors)
        self.assertIn("email", errors)
        self.assertIn("password", errors)
        self.assertIn("phone", errors)
        self.assertIn("course", errors)

    def test_tc03_invalid_email_format(self):
        """Verify registration rejection when email format is invalid."""
        payload = {
            "full_name": "Suresh Raina",
            "email": "suresh_at_invalid_format",
            "password": "ValidPassword123",
            "phone": "9876543210",
            "course": "MCA"
        }

        response = self.client.post(
            '/api/register',
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data["status"], "error")
        self.assertIn("email", data["errors"])
        self.assertIn("Invalid email format", data["errors"]["email"])

    # ------------------------------------------------------------------------
    # TASK E - EXECUTABLE TEST CASE 3: Boundary condition for input length or password length
    # ------------------------------------------------------------------------
    def test_tc04_password_length_boundary(self):
        """
        Verify password length boundary conditions:
        - Boundary Min-1 (7 chars) -> FAIL (400 Bad Request)
        - Boundary Min (8 chars) -> PASS (201 Created)
        """
        # 1. Below boundary (7 characters)
        payload_invalid = {
            "full_name": "Boundary Tester",
            "email": "test.shortpass@example.com",
            "password": "Pass123",  # 7 chars
            "phone": "9876543210",
            "course": "MCA"
        }
        res_fail = self.client.post(
            '/api/register',
            data=json.dumps(payload_invalid),
            content_type='application/json'
        )
        self.assertEqual(res_fail.status_code, 400)
        self.assertIn("Password must be at least 8 characters", res_fail.get_json()["errors"]["password"])

        # 2. Exact minimum boundary (8 characters)
        payload_valid = {
            "full_name": "Boundary Tester",
            "email": "test.minpass@example.com",
            "password": "Pass1234",  # Exactly 8 chars with letter and number
            "phone": "9876543210",
            "course": "MCA"
        }
        res_pass = self.client.post(
            '/api/register',
            data=json.dumps(payload_valid),
            content_type='application/json'
        )
        self.assertEqual(res_pass.status_code, 201)

    def test_tc05_full_name_length_boundary(self):
        """
        Verify student name length boundary conditions:
        - Min boundary (2 characters) -> PASS (201)
        - Exceeding boundary (> 50 characters) -> FAIL (400)
        """
        # Min boundary (2 characters)
        res_min = self.client.post(
            '/api/register',
            data=json.dumps({
                "full_name": "Jo",
                "email": "jo.minname@example.com",
                "password": "Password123",
                "phone": "9123456780",
                "course": "MCA"
            }),
            content_type='application/json'
        )
        self.assertEqual(res_min.status_code, 201)

        # Exceeding boundary (55 characters)
        res_max = self.client.post(
            '/api/register',
            data=json.dumps({
                "full_name": "A" * 55,
                "email": "toolong.name@example.com",
                "password": "Password123",
                "phone": "9123456780",
                "course": "MCA"
            }),
            content_type='application/json'
        )
        self.assertEqual(res_max.status_code, 400)
        self.assertIn("Full name cannot exceed 50 characters", res_max.get_json()["errors"]["full_name"])

    # ------------------------------------------------------------------------
    # ADDITIONAL TESTS: Duplicate email, Phone validation, AI Generator, CSV
    # ------------------------------------------------------------------------
    def test_tc06_duplicate_email_prevention(self):
        """Verify FR3: Duplicate email addresses cannot register twice."""
        # Initial registration is pre-seeded with arun.kumar@example.com
        payload_dup = {
            "full_name": "Arun Kumar Clone",
            "email": "arun.kumar@example.com",
            "password": "SecurePassword1",
            "phone": "9111222333",
            "course": "M.Tech"
        }
        response = self.client.post(
            '/api/register',
            data=json.dumps(payload_dup),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 409)
        self.assertIn("Duplicate Email Error", response.get_json()["message"])

    def test_tc07_invalid_phone_number(self):
        """Verify phone number must be exactly 10 numeric digits."""
        payload = {
            "full_name": "Phone Tester",
            "email": "phone.tester@example.com",
            "password": "Password123",
            "phone": "98765",  # 5 digits only
            "course": "MBA"
        }
        response = self.client.post(
            '/api/register',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Phone number must be exactly 10 numeric digits", response.get_json()["errors"]["phone"])

    def test_tc08_ai_generator_produces_at_least_eight_test_cases(self):
        """Verify AI generator fallback returns at least 8 structured test cases adhering to schema."""
        result = generate_test_cases("FR1", "Student Registration", "System allows registration", force_fallback=True)
        self.assertIn("test_cases", result)
        self.assertIn("engine", result)
        self.assertGreaterEqual(len(result["test_cases"]), 8, "Generator must produce at least 8 structured test cases")

        first_tc = result["test_cases"][0]
        self.assertIn("tc_id", first_tc)
        self.assertIn("req_code", first_tc)
        self.assertIn("scenario", first_tc)
        self.assertIn("test_type", first_tc)
        self.assertIn("input_data", first_tc)
        self.assertIn("expected_result", first_tc)
        self.assertEqual(first_tc["status"], "Not Executed")

    def test_tc09_requirement_crud_lifecycle(self):
        """Verify requirement creation, viewing, updating, and deletion."""
        # 1. Create requirement
        create_res = self.client.post('/api/requirements', json={
            "req_code": "FR99",
            "title": "Two Factor Authentication",
            "category": "Security",
            "description": "Send OTP to user phone"
        })
        self.assertEqual(create_res.status_code, 201)

        # 2. Get requirement
        get_res = self.client.get('/api/requirements/FR99')
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.get_json()["requirement"]["title"], "Two Factor Authentication")

        # 3. Update requirement
        update_res = self.client.put('/api/requirements/FR99', json={
            "title": "2FA via SMS & Authenticator App",
            "category": "Security & MFA",
            "description": "Supports TOTP and SMS fallback"
        })
        self.assertEqual(update_res.status_code, 200)

        # 4. Delete requirement
        del_res = self.client.delete('/api/requirements/FR99')
        self.assertEqual(del_res.status_code, 200)

        # Verify deleted
        get_del = self.client.get('/api/requirements/FR99')
        self.assertEqual(get_del.status_code, 404)

    def test_tc10_controlled_failing_test_and_defect_logging(self):
        """
        Verify controlled test failure condition:
        When expected result is 201 Created but input data is invalid,
        execution must mark FAIL and record a real defect.
        """
        # Create a test case expecting 201 Created but providing an invalid email
        self.client.post('/api/test-cases', json={
            "tc_id": "TC-FAIL-DEMO",
            "req_code": "FR1",
            "scenario": "Verify controlled failure condition for viva demonstration",
            "test_type": "Negative",
            "input_data": json.dumps({
                "full_name": "Fail Tester",
                "email": "invalid_email_format_no_at",
                "password": "Password123",
                "phone": "9876543210",
                "course": "MCA"
            }),
            "expected_result": "HTTP 201 Created: Registration successful."
        })

        # Execute the test case
        exec_res = self.client.post('/api/test-cases/execute-live/TC-FAIL-DEMO')
        self.assertEqual(exec_res.status_code, 200)
        data = exec_res.get_json()
        self.assertEqual(data["test_status"], "FAIL", "Mismatched result must result in FAIL")
        self.assertTrue(len(data["defect_desc"]) > 0)

        # Verify defect was recorded in database
        defects_res = self.client.get('/api/defects')
        defects = defects_res.get_json()["defects"]
        matching_defect = next((d for d in defects if d["tc_id"] == "TC-FAIL-DEMO"), None)
        self.assertIsNotNone(matching_defect, "A real defect must be logged upon test failure")
        self.assertEqual(matching_defect["status"], "Open")

    def test_tc11_bulk_execution_endpoint(self):
        """Verify bulk execution executes automated tests and counts pass/fail accurately."""
        res = self.client.post('/api/test-cases/execute-all-live')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertGreaterEqual(data["executed_count"], 8)
        self.assertIn("passed_count", data)

    def test_tc12_csv_export(self):
        """Verify FR10: Testing report can be exported as a valid CSV file."""
        response = self.client.get('/api/report/export-csv')
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response.content_type)
        content = response.data.decode('utf-8')
        self.assertIn("Test Case ID,Requirement ID", content)
        self.assertIn("TC-REG-01", content)


if __name__ == '__main__':
    unittest.main()
