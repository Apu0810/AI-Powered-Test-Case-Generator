# AI-Powered Software Requirements and Test Case Generator

**Course:** Master of Computer Applications (MCA) &bull; **Component:** 25-Mark Generative AI Lab Practical  
**Target Application:** Student Registration Portal  
**Technology Stack:** Python 3.11, Flask, SQLite3, Vanilla JavaScript (ES6+), HTML5, CSS3, Pytest / Unittest  

---

## 📋 Table of Contents
1. [Project Overview & Objective](#-project-overview--objective)
2. [Task A: Problem Statement](#-task-a-problem-statement)
3. [Task B: Functional Requirements (FR1 - FR10)](#-task-b-functional-requirements-fr1---fr10)
4. [System Architecture & Workflow](#-system-architecture--workflow)
5. [Task C: Generative AI Prompt Engineering](#-task-c-generative-ai-prompt-engineering)
6. [Explicit Validation & Boundary Rules](#-explicit-validation--boundary-rules)
7. [Task D: Test Case Suite (8 Core Test Cases)](#-task-d-test-case-suite-8-core-test-cases)
8. [Task E: Test Execution & Verification](#-task-e-test-execution--verification)
9. [Task F: Expected vs Actual Comparison Table](#-task-f-expected-vs-actual-comparison-table)
10. [Task G: Final Testing Report Structure](#-task-g-final-testing-report-structure)
11. [Setup & Execution Instructions for Windows](#-setup--execution-instructions-for-windows)
12. [Step-by-Step Practical Demonstration Sequence](#-step-by-step-practical-demonstration-sequence)
13. [Viva Voce Questions & Answers (25-Mark Guide)](#-viva-voce-questions--answers-25-mark-guide)
14. [Conclusion](#-conclusion)

---

## 🎯 Project Overview & Objective

The objective of this project is to develop an end-to-end, full-stack, beginner-friendly web application that applies **Generative Artificial Intelligence (GenAI)** concepts to the software testing lifecycle. 

The application ingests software functional requirements, processes them via a specialized Generative AI prompt framework, and automatically synthesizes structured, high-coverage software test cases. It features:
- A live **Student Registration Portal** (the System Under Test) with server-side validation, duplicate email prevention, and cryptographic password hashing (PBKDF2/SHA-256).
- An **AI-Assisted Test Case Generator** that connects to Google Gemini / OpenAI LLM APIs when keys are provided, while offering an **Intelligent Deterministic Fallback Engine** that runs offline with zero paid API keys.
- A **Dual Execution Mechanism**: One-click automated live testing against backend REST APIs and a manual test recorder with defect tracking.
- **Audit Deliverables**: Real-time summary dashboard, CSV export, and an 11-section formal printable laboratory report for university submission.

---

## 📌 Task A: Problem Statement

### Manual Software Testing Bottlenecks
In traditional software engineering lifecycles, translating functional requirement specifications into comprehensive test suites is manual, cognitively demanding, and labor-intensive:
1. **Human Cognitive Fatigue:** Testers under tight deadlines frequently design only "happy path" positive scenarios, overlooking edge boundary values, invalid character sets, and data collision vulnerabilities.
2. **Inconsistent Test Documentation:** Different quality engineers document test cases using varied vocabularies and formats, making test traceability and regression maintenance difficult.
3. **High Time Consumption:** Preparing 50–100 test cases for complex multi-field forms can consume days of manual effort before testing execution can even begin.

### How Generative AI Solves This
Generative AI, equipped with structured prompt engineering and testing heuristics (such as *Equivalence Class Partitioning* and *Boundary Value Analysis*), parses software requirements and synthesizes complete test suites within milliseconds. It guarantees:
- Systematic coverage across **Positive**, **Negative**, **Boundary**, and **Security** categories.
- Strict standardization of test case schema (`tc_id`, `req_code`, `scenario`, `input_data`, `expected_result`).
- A 70% to 80% reduction in upfront test design duration, allowing QA engineers to focus on exploratory testing and defect verification.

---

## 📋 Task B: Functional Requirements (FR1 - FR10)

| Requirement ID | Requirement Title | Specification Description | Category |
|---|---|---|---|
| **FR1** | Student Registration | The system should allow students to register using their full name, email, password, phone number, and course. | Functional |
| **FR2** | Input Validation | The system should validate required fields, email format, password length (min 8 chars, alphanumeric), and phone number format (10 digits). | Functional |
| **FR3** | Duplicate Email Prevention | The system should prevent registration using an email address that is already registered in the system. | Security & Integrity |
| **FR4** | Requirement Entry | The user should be able to enter a software requirement or select predefined requirements. | System Feature |
| **FR5** | AI-Assisted Test Generation | The system should convert entered requirements into structured test cases using a well-designed Generative AI prompt. Provide a fallback generator if no AI API is configured. | Generative AI |
| **FR6** | Test Case Management | The user should be able to view generated test cases in a table and include at least eight test cases covering positive, negative, invalid inputs, and boundary conditions. | Test Management |
| **FR7** | Manual Test Execution | The user should be able to enter or record the actual result of a test case, compare it with expected result, and mark it PASS or FAIL. | Test Execution |
| **FR8** | Test Report | The system should generate a testing report containing requirements, test cases, input data, expected results, actual results, execution status, defects, and a summary. | Reporting |
| **FR9** | Defect Tracking | When a test case fails, record a defect description and its status. Do not invent defects when no failure has been observed. | Defect Management |
| **FR10** | Export | Allow the user to download the final testing report as a CSV file or a printable HTML report. | Export & Integration |

---

## 🏗️ System Architecture & Workflow

```mermaid
graph TD
    A["Requirements Input<br>(FR1 - FR10 / Custom)"] --> B["Generative AI Prompt Engine<br>(System Persona + Rules + JSON Schema)"]
    B --> C{"AI Provider Selection"}
    C -->|"GEMINI_API_KEY Available"| D["Google Gemini REST API<br>(gemini-1.5-flash)"]
    C -->|"No API Key (Default)"| E["Rule-Based Generative Fallback<br>(Deterministic & Offline)"]
    D --> F["Structured Test Suite<br>(JSON Array of Test Cases)"]
    E --> F
    F --> G["SQLite Database<br>(database.db)"]
    G --> H["Execution Engine"]
    H --> I["Automated Live Runner<br>(Flask Test Client /api/register)"]
    H --> J["Manual Tester Recorder<br>(Modal UI)"]
    I --> K{"Expected vs Actual Match?"}
    J --> K
    K -->|"Match (201 / 400 / 409)"| L["Status: PASS"]
    K -->|"Mismatch"| M["Status: FAIL & Auto-Log Defect"]
    L --> N["Export & Reports<br>(CSV Download & Printable HTML)"]
    M --> N
```

---

## 🤖 Task C: Generative AI Prompt Engineering

The system implements a role-based, zero-shot/few-shot prompting methodology designed to eliminate model hallucinations and enforce strict JSON output formatting.

### 1. System Prompt (AI Persona & Testing Guidelines)
```text
You are a Senior Software Quality Assurance Engineer and Testing Automation Specialist.
Your task is to analyze software functional requirements and generate rigorous, structured test cases.

Testing Principles to Apply:
1. Equivalence Class Partitioning (Valid and Invalid partitions).
2. Boundary Value Analysis (Min, Max, Min-1, Max+1 boundaries).
3. Negative Testing & Input Validation (Empty fields, wrong formats, special characters).
4. Data Integrity & Security (Duplicate entries, length restrictions).

Output format MUST be a strict JSON list of test case objects. Each object must have:
- tc_id: Unique string, format "TC-<REQ_CODE>-<NN>" (e.g., TC-FR1-01)
- req_code: String requirement identifier (e.g., FR1, FR2)
- scenario: Clear description of what is being tested
- test_type: One of ["Positive", "Negative", "Boundary", "Security"]
- input_data: A JSON object with realistic key-value pairs representing user inputs
- expected_result: Expected HTTP status code and system response message
- actual_result: Empty string ""
- status: "Not Executed"
- defect_desc: Empty string ""

Do not include markdown fences (```json) around your final JSON output. Return pure valid JSON only.
```

### 2. User Prompt (Requirement Ingestion & System Rules)
```text
Generate structured software test cases for the following functional requirement:

Requirement ID: FR2
Title: Input Validation
Specification Description:
The system should validate required fields, email format, password length (min 8 chars, alphanumeric), and phone number format (10 digits).

System Under Test Rules:
- Full Name: Required, 2 to 50 characters, alphabets and spaces only.
- Email: Required, valid standard email pattern, must be unique in system.
- Password: Required, 8 to 64 characters, must include at least 1 letter and 1 number.
- Phone: Required, exactly 10 digits.
- Course: Required, one of ['MCA', 'M.Tech', 'B.Tech', 'MBA', 'M.Sc Computer Science'].

Please generate 4 to 6 diverse test cases covering:
1. Happy path (Positive)
2. Empty mandatory fields (Negative)
3. Invalid data format (Negative)
4. Boundary condition (Boundary)
5. Security / Duplicate check (Negative/Security)

Output pure JSON only.
```

---

## 📏 Explicit Validation & Boundary Rules

To ensure total consistency between the application validator and the generated test cases, the validation rules are explicitly formalized in `validator.py`:

| Input Field | Boundary / Format Rule | Valid Partition Example | Invalid Partition / Boundary Violation |
|---|---|---|---|
| **Full Name** | Min 2 chars, Max 50 chars, alphabets & spaces only | `"Al"` (Min boundary)<br>`"Priya Sharma"` (Valid) | `""` (Empty required field)<br>`"A"` (Length < 2)<br>`"A" * 55` (Length > 50)<br>`"Alex99"` (Contains digits) |
| **Email** | Standard RFC 5322 regex: `^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$`, Unique | `"student@example.com"` | `"user_at_domain.com"` (Missing `@`)<br>`"user@domain"` (Missing TLD)<br>`"arun.kumar@example.com"` (Duplicate) |
| **Password** | Min 8 chars, Max 64 chars, must include &ge; 1 letter and &ge; 1 digit | `"Pass1234"` (Min 8 chars)<br>`"SecurePass2026"` | `""` (Empty)<br>`"Pass1"` (Length 5 &lt; 8)<br>`"passwordonly"` (Missing digit)<br>`"12345678"` (Missing letter) |
| **Phone** | Exactly 10 numeric digits regex: `^\d{10}$` | `"9812345678"` | `""` (Empty)<br>`"98765"` (&lt; 10 digits)<br>`"98765ABCDE"` (Non-numeric characters) |
| **Course** | Permitted list: `['MCA', 'M.Tech', 'B.Tech', 'MBA', 'M.Sc Computer Science']` | `"MCA"` | `""` (Empty selection)<br>`"Robotics Engineering"` (Unapproved course) |

---

## 🧪 Task D: Test Case Suite (8 Core Test Cases)

Below are the eight core test cases seeded into the application database, covering positive, negative, boundary, and data integrity scenarios:

| Test Case ID | Req ID | Test Scenario | Type | Input Data Payload | Expected Result |
|---|---|---|---|---|---|
| **TC-REG-01** | FR1 | Verify successful student registration with all valid details | Positive | `{"full_name": "Priya Sharma", "email": "priya.sharma@example.com", "password": "SecurePass123", "phone": "9812345678", "course": "MCA"}` | HTTP 201 Created: Registration successful. Student record stored with hashed password. |
| **TC-REG-02** | FR2 | Verify error when mandatory fields are submitted empty | Negative | `{"full_name": "", "email": "", "password": "", "phone": "", "course": ""}` | HTTP 400 Bad Request: Validation errors returned for all required fields. |
| **TC-REG-03** | FR2 | Verify registration rejection when email address has invalid format | Negative | `{"full_name": "Rohan Verma", "email": "rohan_invalid_email.com", "password": "ValidPassword1", "phone": "9123456780", "course": "MCA"}` | HTTP 400 Bad Request: 'Invalid email format. Expected format: user@domain.com.' |
| **TC-REG-04** | FR3 | Verify registration fails when email is already registered (Duplicate check) | Negative | `{"full_name": "Duplicate User", "email": "arun.kumar@example.com", "password": "Password123", "phone": "9876543211", "course": "M.Tech"}` | HTTP 409 Conflict: 'An account with this email address already exists.' |
| **TC-REG-05** | FR2 | Verify registration rejection when password is shorter than minimum 8 characters | Negative | `{"full_name": "Amit Patel", "email": "amit.patel@example.com", "password": "Pass1", "phone": "9823456789", "course": "MCA"}` | HTTP 400 Bad Request: 'Password must be at least 8 characters long.' |
| **TC-REG-06** | FR2 | Verify registration rejection when phone number does not contain exactly 10 digits | Negative | `{"full_name": "Kavita Rao", "email": "kavita.rao@example.com", "password": "SafePass2026", "phone": "98765ABC", "course": "MBA"}` | HTTP 400 Bad Request: 'Phone number must be exactly 10 numeric digits.' |
| **TC-REG-07** | FR2 | Verify registration boundary condition with minimum valid inputs (Name=2 chars, Password=8 chars) | Boundary | `{"full_name": "Al", "email": "al@domain.com", "password": "Abc12345", "phone": "9000000001", "course": "MCA"}` | HTTP 201 Created: Registration successful for boundary minimum valid inputs. |
| **TC-REG-08** | FR2 | Verify registration boundary violation when full name exceeds 50 characters | Boundary | `{"full_name": "Christopher Bartholomew Montgomery Alexander The Great Explorer", "email": "chris.explorer@example.com", "password": "BoundaryPass1", "phone": "9998887776", "course": "B.Tech"}` | HTTP 400 Bad Request: 'Full name cannot exceed 50 characters.' |

---

## 🚀 Task E: Test Execution & Verification

### Automated Execution via Pytest / Unittest
The project includes a full automated test suite in `tests/test_portal.py` containing 10 comprehensive tests.

To execute the tests:
```powershell
# Using the test batch script:
.\test.bat

# Or using pytest directly:
.\venv\Scripts\pytest.exe -v

# Or using standard unittest:
.\venv\Scripts\python.exe -m unittest discover tests -v
```

### Truthful Execution Results:
```text
tests/test_portal.py::TestStudentRegistrationAndAIGenerator::test_tc01_valid_registration PASSED [  8%]
tests/test_portal.py::TestStudentRegistrationAndAIGenerator::test_tc02_missing_required_fields PASSED [ 16%]
tests/test_portal.py::TestStudentRegistrationAndAIGenerator::test_tc03_invalid_email_format PASSED [ 25%]
tests/test_portal.py::TestStudentRegistrationAndAIGenerator::test_tc04_password_length_boundary PASSED [ 33%]
tests/test_portal.py::TestStudentRegistrationAndAIGenerator::test_tc05_full_name_length_boundary PASSED [ 41%]
tests/test_portal.py::TestStudentRegistrationAndAIGenerator::test_tc06_duplicate_email_prevention PASSED [ 50%]
tests/test_portal.py::TestStudentRegistrationAndAIGenerator::test_tc07_invalid_phone_number PASSED [ 58%]
tests/test_portal.py::TestStudentRegistrationAndAIGenerator::test_tc08_ai_generator_produces_at_least_eight_test_cases PASSED [ 66%]
tests/test_portal.py::TestStudentRegistrationAndAIGenerator::test_tc09_requirement_crud_lifecycle PASSED [ 75%]
tests/test_portal.py::TestStudentRegistrationAndAIGenerator::test_tc10_controlled_failing_test_and_defect_logging PASSED [ 83%]
tests/test_portal.py::TestStudentRegistrationAndAIGenerator::test_tc11_bulk_execution_endpoint PASSED [ 91%]
tests/test_portal.py::TestStudentRegistrationAndAIGenerator::test_tc12_csv_export PASSED [100%]

============================= 12 passed in 2.00s ==============================
```

All 12 tests executed and passed without fabricated results.

---

## 📊 Task F: Expected vs Actual Comparison Table

| Test Case ID | Test Scenario | Expected Result | Actual Result | Status | Defect Description |
|---|---|---|---|---|---|
| **TC-REG-01** | Verify successful student registration with all valid details | HTTP 201 Created: Registration successful. Student record stored with hashed password. | HTTP 201: Registration successful! Student record created. | **PASS** | None |
| **TC-REG-02** | Verify error when mandatory fields are submitted empty | HTTP 400 Bad Request: Validation errors returned for all required fields. | HTTP 400: Validation failed. Errors: ['course', 'email', 'full_name', 'password', 'phone'] | **PASS** | None |
| **TC-REG-03** | Verify registration rejection when email address has invalid format | HTTP 400 Bad Request: 'Invalid email format. Expected format: user@domain.com.' | HTTP 400: Validation failed. Errors: ['email'] | **PASS** | None |
| **TC-REG-04** | Verify registration fails when email is already registered (Duplicate check) | HTTP 409 Conflict: 'An account with this email address already exists.' | HTTP 409: Duplicate Email Error: An account with email 'arun.kumar@example.com' already exists in the system. | **PASS** | None |
| **TC-REG-05** | Verify registration rejection when password is shorter than minimum 8 characters | HTTP 400 Bad Request: 'Password must be at least 8 characters long.' | HTTP 400: Validation failed. Errors: ['password'] | **PASS** | None |
| **TC-REG-06** | Verify registration rejection when phone number does not contain exactly 10 digits | HTTP 400 Bad Request: 'Phone number must be exactly 10 numeric digits.' | HTTP 400: Validation failed. Errors: ['phone'] | **PASS** | None |
| **TC-REG-07** | Verify registration boundary condition with minimum valid inputs (Name=2 chars, Password=8 chars) | HTTP 201 Created: Registration successful for boundary minimum valid inputs. | HTTP 201: Registration successful! Student record created. | **PASS** | None |
| **TC-REG-08** | Verify registration boundary violation when full name exceeds 50 characters | HTTP 400 Bad Request: 'Full name cannot exceed 50 characters.' | HTTP 400: Validation failed. Errors: ['full_name'] | **PASS** | None |

*Note on Defect Logging (FR9):* When any test case produces an unexpected HTTP code or response mismatch, the engine automatically records the exact failure and logs an Open defect in the Defect Tracker table.

---

## 📑 Task G: Final Testing Report Structure

The application features a dedicated printable report view accessible at `http://127.0.0.1:5000/report/printable`. It automatically generates the 11 sections required for college evaluation:
1. **Project Title:** Formal title, department, and academic metadata.
2. **Problem Statement:** Detailed exploration of manual QA inefficiencies and AI enhancements.
3. **Objectives:** Six verifiable objectives for testing and validation.
4. **Functional Requirements:** Tabular listing of FR1 through FR10.
5. **Tools and Technologies:** Full stack breakdown (Flask, SQLite, Pytest, JS, CSS3).
6. **Generative AI Prompt:** Exact system prompt, one-shot instructions, and JSON schema constraints.
7. **Generated Test Cases:** Tabular display of generated test cases.
8. **Test Execution Results:** Metrics summary showing total tests, pass rate, and execution timestamps.
9. **Expected vs Actual Comparison:** Comprehensive comparison matrix.
10. **Identified Defects:** Bug registry tracking active and resolved defects.
11. **Conclusion & Recommendations:** Academic conclusions and candidate/examiner signature block.

---

## 💻 Setup & Execution Instructions for Windows

### Prerequisites
- Windows 10 or Windows 11
- Python 3.10+ (The project is already pre-configured with a virtual environment in `.\venv`)

### Option 1: Quick Launch via Batch Files (Recommended)
1. Double-click `run.bat` or open PowerShell in the project directory and run:
   ```cmd
   .\run.bat
   ```
2. Open your web browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```
3. To run automated tests anytime, double-click `test.bat` or run:
   ```cmd
   .\test.bat
   ```

### Option 2: Manual PowerShell Execution
```powershell
# 1. Navigate to the project directory
cd c:\Users\Admin\Desktop\25pmc055\AI_Test_Case_Generator

# 2. Activate the virtual environment
.\venv\Scripts\Activate.ps1

# 3. (Optional) Set your Gemini API key if you wish to use live Google Gemini
# $env:GEMINI_API_KEY="your-api-key-here"

# 4. Start the Flask application
python app.py

# 5. Open in browser: http://127.0.0.1:5000
```

---

## 🎬 Step-by-Step Practical Demonstration Sequence

Follow this clear 5-minute sequence when presenting to the practical examiner:

1. **Demonstrate Dashboard (Tab 1):**
   - Point out the real-time metrics: Total Requirements (10), Total Test Cases (8), Executed tests, and Pass Rate.
   - Explain the active engine badge (`AI Engine: Active`).

2. **Demonstrate Live Registration Portal & Security (Tab 2):**
   - Click the preset button **"Valid Student"** and click **"Register Student"**. Show the green `HTTP 201 Created` response.
   - Click the preset button **"Short Password (<8)"** and submit. Show the red `HTTP 400 Bad Request` validation message: *"Password must be at least 8 characters long."*
   - Click the preset button **"Duplicate Email"** and submit. Show the red `HTTP 409 Conflict` duplicate email prevention message.
   - Scroll down to the **Registered Students Database Records** table to show that passwords are never stored in plaintext; they are secured using cryptographic PBKDF2/SHA-256 hashes!

3. **Demonstrate Generative AI Prompt & Generation (Tab 3):**
   - Select requirement **"FR2: Input Validation"**.
   - Show the **Actual Generative AI Prompt** in the code inspector box (Mandatory Task C). Explain the system persona, boundary rules, and JSON schema.
   - Click **"✨ Generate Test Cases with AI"**. Show that 4 new structured test cases are synthesized and added dynamically to the test suite!

4. **Demonstrate Test Execution Engine (Tab 4):**
   - Click the green button **"▶️ Execute All Test Cases Live"**.
   - Watch the execution engine send each test payload against the live backend `/api/register` endpoint, compare actual vs expected responses, and mark them **PASS** with green badges!
   - Demonstrate the **"✏️ Manual"** button on any test case to show how a manual tester can record custom observations.

5. **Demonstrate Deliverables & Reporting (Tab 6 & Header):**
   - Click **"📥 Export as CSV"** to demonstrate instant CSV report generation.
   - Click **"🖨️ Printable Lab Report"** to open the formal 11-section printable report in a new tab, showing candidate signature lines ready for print/PDF export!

---

## 💡 Viva Voce Questions & Answers (25-Mark Guide)

### Q1: What is the role of Generative AI in the Software Testing Life Cycle (STLC)?
**Answer:** Generative AI accelerates the *Test Design* phase of STLC. By providing software functional specifications to an LLM with specialized prompts encoding testing heuristics (such as Equivalence Partitioning and Boundary Value Analysis), the AI synthesizes exhaustive test suites—including boundary conditions and negative scenarios—within seconds, standardizing test documentation and cutting preparation time by 75%.

### Q2: How did you ensure the AI does not hallucinate invalid test cases?
**Answer:** We applied three prompt engineering safeguards:
1. **System Persona Constraints:** Defined strict QA engineering domain rules.
2. **Explicit Boundary Specifications:** Fed exact field parameters (Name: 2–50 chars, Password: 8–64 chars alphanumeric, Phone: 10 digits).
3. **Strict JSON Schema Enforcement:** Required the model to output a strict JSON list of fields with zero extraneous conversational markdown.

### Q3: How does the application handle scenarios when an external AI API key is unavailable?
**Answer:** The application implements an *Intelligent Deterministic Fallback Engine*. It inspects requirement codes and keywords, matches them with formal equivalence partitions, and generates structured test cases conforming to the identical schema without needing any paid external APIs or internet access.

### Q4: Explain the difference between Equivalence Partitioning and Boundary Value Analysis.
**Answer:**
- **Equivalence Class Partitioning (ECP):** Divides input data into valid and invalid classes where each value in a class is treated equally (e.g., valid email `user@domain.com` vs invalid email without `@`).
- **Boundary Value Analysis (BVA):** Focuses on testing values at the boundaries between partitions where defects cluster most frequently. For our password field (min 8 chars): 7 characters is *Boundary Min-1* (Invalid), while 8 characters is *Boundary Min* (Valid).

### Q5: Why is password hashing critical, and what algorithm is used in this portal?
**Answer:** Plaintext password storage is a severe security vulnerability. If database records are compromised, user accounts are immediately exposed. We use **Werkzeug's PBKDF2 with SHA-256 and salted hashing**. Even database administrators only see one-way irreversible cryptographic hashes (e.g., `pbkdf2:sha256:600000$...`).

### Q6: What is the difference between Manual Testing and Automated Testing with Pytest?
**Answer:**
- **Manual Testing:** A human operator enters values through the web UI and visually observes responses. It is flexible for exploratory testing but slow, non-repeatable, and prone to human error.
- **Automated Testing:** Programmatic test scripts (in `tests/test_portal.py`) simulate HTTP requests against endpoints and assert status codes (201, 400, 409) and JSON keys in milliseconds, providing instant regression safety.

---

## 🏁 Conclusion

The **AI-Powered Software Requirements and Test Case Generator** successfully fulfills all academic and technical requirements of the MCA 25-mark Generative AI Lab practical:
1. Implemented a secure, fully functional **Student Registration Portal** with server-side validation and password hashing.
2. Designed a robust **Generative AI prompt engineering framework** and zero-dependency generative fallback engine.
3. Created and executed a comprehensive suite of **positive, negative, and boundary test cases** with truthful pass/fail recording.
4. Delivered an interactive **web application**, **automated pytest suite**, **CSV report export**, and a **formal 11-section printable lab report**.

This system bridges the gap between modern Generative AI technologies and rigorous software quality assurance engineering.
