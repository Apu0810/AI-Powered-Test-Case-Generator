"""
Generative AI Test Case Generator Module
Implements prompt engineering, LLM API integration (Gemini / OpenAI),
and an intelligent, transparent local keyword & rule-based generative fallback.
"""
import os
import json
import re
import requests

# Base System Prompt defining the AI Persona, Testing Rules, and Output Schema
SYSTEM_PROMPT = """You are a Senior Software Quality Assurance Engineer and Testing Automation Specialist.
Your task is to analyze software functional requirements and generate rigorous, structured test cases.

Testing Principles to Apply:
1. Equivalence Class Partitioning (Valid and Invalid partitions).
2. Boundary Value Analysis (Min, Max, Min-1, Max+1 boundaries).
3. Negative Testing & Input Validation (Empty fields, wrong formats, special characters).
4. Data Integrity & Security (Duplicate entries, length restrictions).

Output format MUST be a strict JSON list of at least 8 test case objects. Each object must have:
- tc_id: Unique string, format "TC-<REQ_CODE>-<NN>" (e.g., TC-FR1-01)
- req_code: String requirement identifier (e.g., FR1, FR2)
- scenario: Clear description of what is being tested
- test_type: One of ["Positive", "Negative", "Boundary", "Security"]
- input_data: A JSON object with realistic key-value pairs representing user inputs
- expected_result: Expected HTTP status code and system response message
- actual_result: Empty string ""
- status: "Not Executed"
- defect_desc: Empty string ""

Do not include markdown fences (```json) around your final JSON output. Return pure valid JSON only."""


def get_prompt_template(req_code="FR1", req_title="Student Registration", req_desc="Student enters registration details"):
    """
    Returns the exact formatted prompt string sent to the Generative AI model.
    Used for UI inspection (Mandatory Task C).
    """
    return f"""=== SYSTEM PROMPT ===
{SYSTEM_PROMPT}

=== USER PROMPT ===
Generate at least 8 structured software test cases for the following functional requirement:

Requirement ID: {req_code}
Title: {req_title}
Specification Description:
{req_desc}

System Under Test Rules (Student Registration Portal):
- Full Name: Required, 2 to 50 characters, alphabets and spaces only.
- Email: Required, valid standard email pattern, must be unique in system.
- Password: Required, 8 to 64 characters, must include at least 1 letter and 1 number.
- Phone: Required, exactly 10 digits.
- Course: Required, one of ['MCA', 'M.Tech', 'B.Tech', 'MBA', 'M.Sc Computer Science'].

Please generate at least 8 diverse test cases covering:
1. Positive Happy Path
2. Empty Mandatory Fields (Negative)
3. Invalid Data Format (Negative)
4. Duplicate / Integrity Conflict (Negative/Security)
5. Boundary Minimum Valid Input (Boundary)
6. Boundary Minimum-1 Invalid Input (Boundary)
7. Boundary Maximum Valid Limit (Boundary)
8. Boundary Exceeding Limit (Boundary)

Output pure JSON only."""


def generate_test_cases(req_code, req_title, req_desc, force_fallback=False):
    """
    Generates at least 8 test cases for a given requirement.
    Attempts LLM API call if API keys are set, otherwise transparently invokes the
    Local Rule & Keyword-Based Fallback Generator.
    
    Returns:
        dict: {
            "test_cases": list of dicts,
            "engine": str ("Google Gemini Live API" | "OpenAI Live API" | "Local Rule & Keyword-Based Fallback Generator (Offline)"),
            "prompt_used": str
        }
    """
    prompt = get_prompt_template(req_code, req_title, req_desc)
    
    # Check for API keys
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    openai_key = os.environ.get("OPENAI_API_KEY", "").strip()

    if not force_fallback and gemini_key:
        try:
            test_cases = _call_gemini_api(gemini_key, prompt)
            if test_cases and len(test_cases) >= 4:
                return {
                    "test_cases": test_cases,
                    "engine": "Google Gemini Live API (gemini-1.5-flash)",
                    "prompt_used": prompt
                }
        except Exception as e:
            print(f"[Notice] Gemini API call unsuccessful: {e}. Activating Local Fallback Generator.")

    if not force_fallback and openai_key:
        try:
            test_cases = _call_openai_api(openai_key, prompt)
            if test_cases and len(test_cases) >= 4:
                return {
                    "test_cases": test_cases,
                    "engine": "OpenAI Live API (gpt-3.5-turbo)",
                    "prompt_used": prompt
                }
        except Exception as e:
            print(f"[Notice] OpenAI API call unsuccessful: {e}. Activating Local Fallback Generator.")

    # Transparent Local Fallback Generator (Never pretends to be a live cloud LLM)
    test_cases = _keyword_aware_fallback_generator(req_code, req_title, req_desc)
    return {
        "test_cases": test_cases,
        "engine": "Local Rule & Keyword-Based Fallback Generator (Offline - No API Required)",
        "prompt_used": prompt
    }


def _call_gemini_api(api_key, prompt_text):
    """Calls Gemini REST endpoint."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{
            "parts": [{"text": prompt_text}]
        }],
        "generationConfig": {
            "temperature": 0.2,
            "topP": 0.8
        }
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=12)
    resp.raise_for_status()
    data = resp.json()
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    return _parse_json_from_llm(text)


def _call_openai_api(api_key, prompt_text):
    """Calls OpenAI REST endpoint."""
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt_text}
        ],
        "temperature": 0.2
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=12)
    resp.raise_for_status()
    data = resp.json()
    text = data["choices"][0]["message"]["content"]
    return _parse_json_from_llm(text)


def _parse_json_from_llm(text):
    """Cleans markdown fences and parses JSON from model output."""
    clean_text = text.strip()
    if clean_text.startswith("```json"):
        clean_text = clean_text[7:]
    elif clean_text.startswith("```"):
        clean_text = clean_text[3:]
    if clean_text.endswith("```"):
        clean_text = clean_text[:-3]
    clean_text = clean_text.strip()
    parsed = json.loads(clean_text)
    if isinstance(parsed, list):
        return parsed
    elif isinstance(parsed, dict) and "test_cases" in parsed:
        return parsed["test_cases"]
    return []


def _keyword_aware_fallback_generator(req_code, req_title, req_desc):
    """
    Transparent, deterministic Local Fallback Generator.
    Synthesizes at least 8 relevant, structured test cases based on requirement keywords,
    covering Positive, Negative, Invalid inputs, Boundary conditions, and Security scenarios.
    """
    code = req_code.upper().strip()
    combined = f"{code} {req_title} {req_desc}".lower()

    # 1. Student Registration (FR1 or keywords registration/signup/register)
    if "fr1" in code.lower() or "registration" in combined or "signup" in combined or "register" in combined:
        return [
            {
                "tc_id": f"TC-{code}-01",
                "req_code": code,
                "scenario": "Verify successful student registration with all valid mandatory inputs",
                "test_type": "Positive",
                "input_data": json.dumps({
                    "full_name": "Divya Nair",
                    "email": "divya.nair@example.com",
                    "password": "Password2026",
                    "phone": "9871122334",
                    "course": "MCA"
                }),
                "expected_result": "HTTP 201 Created: Registration successful. Student record saved.",
                "actual_result": "",
                "status": "Not Executed",
                "defect_desc": ""
            },
            {
                "tc_id": f"TC-{code}-02",
                "req_code": code,
                "scenario": "Verify system response when all registration fields are submitted empty",
                "test_type": "Negative",
                "input_data": json.dumps({
                    "full_name": "",
                    "email": "",
                    "password": "",
                    "phone": "",
                    "course": ""
                }),
                "expected_result": "HTTP 400 Bad Request: Validation errors for full_name, email, password, phone, course.",
                "actual_result": "",
                "status": "Not Executed",
                "defect_desc": ""
            },
            {
                "tc_id": f"TC-{code}-03",
                "req_code": code,
                "scenario": "Verify rejection when submitting invalid course not in approved curriculum",
                "test_type": "Negative",
                "input_data": json.dumps({
                    "full_name": "Siddharth Sen",
                    "email": "siddharth@example.com",
                    "password": "SecurePass123",
                    "phone": "9845012345",
                    "course": "Robotics Engineering"
                }),
                "expected_result": "HTTP 400 Bad Request: 'Course must be one of: MCA, M.Tech, B.Tech, MBA, M.Sc Computer Science.'",
                "actual_result": "",
                "status": "Not Executed",
                "defect_desc": ""
            },
            {
                "tc_id": f"TC-{code}-04",
                "req_code": code,
                "scenario": "Verify duplicate registration rejection when email already exists",
                "test_type": "Negative",
                "input_data": json.dumps({
                    "full_name": "Arun Kumar Clone",
                    "email": "arun.kumar@example.com",
                    "password": "Password123",
                    "phone": "9876543210",
                    "course": "MCA"
                }),
                "expected_result": "HTTP 409 Conflict: 'An account with this email address already exists.'",
                "actual_result": "",
                "status": "Not Executed",
                "defect_desc": ""
            },
            {
                "tc_id": f"TC-{code}-05",
                "req_code": code,
                "scenario": "Verify registration boundary with minimum allowable name length (2 characters)",
                "test_type": "Boundary",
                "input_data": json.dumps({
                    "full_name": "Al",
                    "email": "al.student@domain.com",
                    "password": "Password123",
                    "phone": "9123456789",
                    "course": "MCA"
                }),
                "expected_result": "HTTP 201 Created: Registration successful.",
                "actual_result": "",
                "status": "Not Executed",
                "defect_desc": ""
            },
            {
                "tc_id": f"TC-{code}-06",
                "req_code": code,
                "scenario": "Verify password boundary rejection when length is less than 8 characters",
                "test_type": "Boundary",
                "input_data": json.dumps({
                    "full_name": "Sunil Verma",
                    "email": "sunil.verma@example.com",
                    "password": "Pass1",
                    "phone": "9823456789",
                    "course": "MCA"
                }),
                "expected_result": "HTTP 400 Bad Request: 'Password must be at least 8 characters long.'",
                "actual_result": "",
                "status": "Not Executed",
                "defect_desc": ""
            },
            {
                "tc_id": f"TC-{code}-07",
                "req_code": code,
                "scenario": "Verify phone number rejection when containing non-numeric characters",
                "test_type": "Negative",
                "input_data": json.dumps({
                    "full_name": "Pooja Mehta",
                    "email": "pooja.mehta@example.com",
                    "password": "Password123",
                    "phone": "987654ABCD",
                    "course": "MBA"
                }),
                "expected_result": "HTTP 400 Bad Request: 'Phone number must be exactly 10 numeric digits.'",
                "actual_result": "",
                "status": "Not Executed",
                "defect_desc": ""
            },
            {
                "tc_id": f"TC-{code}-08",
                "req_code": code,
                "scenario": "Verify boundary violation when student full name exceeds 50 characters",
                "test_type": "Boundary",
                "input_data": json.dumps({
                    "full_name": "A" * 55,
                    "email": "boundary.max@example.com",
                    "password": "Password123",
                    "phone": "9998887776",
                    "course": "B.Tech"
                }),
                "expected_result": "HTTP 400 Bad Request: 'Full name cannot exceed 50 characters.'",
                "actual_result": "",
                "status": "Not Executed",
                "defect_desc": ""
            }
        ]

    # 2. Input Validation (FR2 or keywords validation/validate/format)
    elif "fr2" in code.lower() or "validation" in combined or "validate" in combined:
        return [
            {
                "tc_id": f"TC-{code}-01",
                "req_code": code,
                "scenario": "Verify validation error when email format is missing domain extension",
                "test_type": "Negative",
                "input_data": json.dumps({
                    "full_name": "Sneha Roy",
                    "email": "sneha@invalid",
                    "password": "Password123",
                    "phone": "9876543210",
                    "course": "MCA"
                }),
                "expected_result": "HTTP 400 Bad Request: 'Invalid email format. Expected format: user@domain.com.'",
                "actual_result": "",
                "status": "Not Executed",
                "defect_desc": ""
            },
            {
                "tc_id": f"TC-{code}-02",
                "req_code": code,
                "scenario": "Verify validation rejection when password contains letters only with no numbers",
                "test_type": "Negative",
                "input_data": json.dumps({
                    "full_name": "Sneha Roy",
                    "email": "sneha.roy@example.com",
                    "password": "LettersOnlyPassword",
                    "phone": "9876543210",
                    "course": "MCA"
                }),
                "expected_result": "HTTP 400 Bad Request: 'Password must contain at least one letter and one number.'",
                "actual_result": "",
                "status": "Not Executed",
                "defect_desc": ""
            },
            {
                "tc_id": f"TC-{code}-03",
                "req_code": code,
                "scenario": "Verify validation rejection when phone number has fewer than 10 digits",
                "test_type": "Boundary",
                "input_data": json.dumps({
                    "full_name": "Pooja Mehta",
                    "email": "pooja.mehta@example.com",
                    "password": "Password123",
                    "phone": "987654321",
                    "course": "MBA"
                }),
                "expected_result": "HTTP 400 Bad Request: 'Phone number must be exactly 10 numeric digits.'",
                "actual_result": "",
                "status": "Not Executed",
                "defect_desc": ""
            },
            {
                "tc_id": f"TC-{code}-04",
                "req_code": code,
                "scenario": "Verify validation rejection when student full name contains numeric characters",
                "test_type": "Negative",
                "input_data": json.dumps({
                    "full_name": "Alex99 Johnson",
                    "email": "alex99@example.com",
                    "password": "Password123",
                    "phone": "9876543210",
                    "course": "B.Tech"
                }),
                "expected_result": "HTTP 400 Bad Request: 'Full name must contain only alphabets and spaces.'",
                "actual_result": "",
                "status": "Not Executed",
                "defect_desc": ""
            },
            {
                "tc_id": f"TC-{code}-05",
                "req_code": code,
                "scenario": "Verify boundary condition for exact minimum valid password length (8 characters)",
                "test_type": "Boundary",
                "input_data": json.dumps({
                    "full_name": "Valid Tester",
                    "email": "valid.boundary@example.com",
                    "password": "Pass1234",
                    "phone": "9876543210",
                    "course": "MCA"
                }),
                "expected_result": "HTTP 201 Created: Registration successful.",
                "actual_result": "",
                "status": "Not Executed",
                "defect_desc": ""
            },
            {
                "tc_id": f"TC-{code}-06",
                "req_code": code,
                "scenario": "Verify validation error when email is missing the '@' symbol",
                "test_type": "Negative",
                "input_data": json.dumps({
                    "full_name": "Ramanujan K",
                    "email": "ramanujan.example.com",
                    "password": "Password123",
                    "phone": "9876543210",
                    "course": "M.Sc Computer Science"
                }),
                "expected_result": "HTTP 400 Bad Request: 'Invalid email format. Expected format: user@domain.com.'",
                "actual_result": "",
                "status": "Not Executed",
                "defect_desc": ""
            },
            {
                "tc_id": f"TC-{code}-07",
                "req_code": code,
                "scenario": "Verify rejection when full name is only a single character (below min boundary 2)",
                "test_type": "Boundary",
                "input_data": json.dumps({
                    "full_name": "A",
                    "email": "single.letter@example.com",
                    "password": "Password123",
                    "phone": "9876543210",
                    "course": "MCA"
                }),
                "expected_result": "HTTP 400 Bad Request: 'Full name must be at least 2 characters.'",
                "actual_result": "",
                "status": "Not Executed",
                "defect_desc": ""
            },
            {
                "tc_id": f"TC-{code}-08",
                "req_code": code,
                "scenario": "Verify boundary acceptance for maximum allowed full name length (50 characters)",
                "test_type": "Boundary",
                "input_data": json.dumps({
                    "full_name": "A" * 50,
                    "email": "fifty.chars@example.com",
                    "password": "Password123",
                    "phone": "9876543210",
                    "course": "MCA"
                }),
                "expected_result": "HTTP 201 Created: Registration successful.",
                "actual_result": "",
                "status": "Not Executed",
                "defect_desc": ""
            }
        ]

    # 3. Duplicate Prevention (FR3 or keywords duplicate/unique)
    elif "fr3" in code.lower() or "duplicate" in combined or "unique" in combined:
        return [
            {
                "tc_id": f"TC-{code}-01",
                "req_code": code,
                "scenario": "Verify rejection when registering with an email already present in database",
                "test_type": "Negative",
                "input_data": json.dumps({
                    "full_name": "Duplicate Tester",
                    "email": "arun.kumar@example.com",
                    "password": "Password123",
                    "phone": "9876543210",
                    "course": "MCA"
                }),
                "expected_result": "HTTP 409 Conflict: 'An account with this email address already exists.'",
                "actual_result": "",
                "status": "Not Executed",
                "defect_desc": ""
            },
            {
                "tc_id": f"TC-{code}-02",
                "req_code": code,
                "scenario": "Verify case-insensitive duplicate email detection (ARUN.KUMAR@EXAMPLE.COM)",
                "test_type": "Negative",
                "input_data": json.dumps({
                    "full_name": "Uppercase Email User",
                    "email": "ARUN.KUMAR@EXAMPLE.COM",
                    "password": "Password123",
                    "phone": "9876543210",
                    "course": "MCA"
                }),
                "expected_result": "HTTP 409 Conflict: 'An account with this email address already exists.'",
                "actual_result": "",
                "status": "Not Executed",
                "defect_desc": ""
            },
            {
                "tc_id": f"TC-{code}-03",
                "req_code": code,
                "scenario": "Verify whitespace-padded duplicate email detection (' arun.kumar@example.com ')",
                "test_type": "Negative",
                "input_data": json.dumps({
                    "full_name": "Whitespace Email User",
                    "email": " arun.kumar@example.com ",
                    "password": "Password123",
                    "phone": "9876543210",
                    "course": "MCA"
                }),
                "expected_result": "HTTP 409 Conflict: 'An account with this email address already exists.'",
                "actual_result": "",
                "status": "Not Executed",
                "defect_desc": ""
            },
            {
                "tc_id": f"TC-{code}-04",
                "req_code": code,
                "scenario": "Verify successful registration with a completely unique new email address",
                "test_type": "Positive",
                "input_data": json.dumps({
                    "full_name": "Unique Student",
                    "email": "unique.student2026@example.com",
                    "password": "UniquePass123",
                    "phone": "9876500112",
                    "course": "MCA"
                }),
                "expected_result": "HTTP 201 Created: Registration successful.",
                "actual_result": "",
                "status": "Not Executed",
                "defect_desc": ""
            },
            {
                "tc_id": f"TC-{code}-05",
                "req_code": code,
                "scenario": "Verify duplicate rejection applies across different course enrollments",
                "test_type": "Negative",
                "input_data": json.dumps({
                    "full_name": "Arun Kumar New Course",
                    "email": "arun.kumar@example.com",
                    "password": "Password123",
                    "phone": "9876543210",
                    "course": "M.Tech"
                }),
                "expected_result": "HTTP 409 Conflict: 'An account with this email address already exists.'",
                "actual_result": "",
                "status": "Not Executed",
                "defect_desc": ""
            },
            {
                "tc_id": f"TC-{code}-06",
                "req_code": code,
                "scenario": "Verify duplicate rejection applies when phone number is different but email is identical",
                "test_type": "Negative",
                "input_data": json.dumps({
                    "full_name": "Arun Kumar Alternate Phone",
                    "email": "arun.kumar@example.com",
                    "password": "Password123",
                    "phone": "9111222333",
                    "course": "MCA"
                }),
                "expected_result": "HTTP 409 Conflict: 'An account with this email address already exists.'",
                "actual_result": "",
                "status": "Not Executed",
                "defect_desc": ""
            },
            {
                "tc_id": f"TC-{code}-07",
                "req_code": code,
                "scenario": "Verify simultaneous duplicate submission prevention via database UNIQUE constraint",
                "test_type": "Security",
                "input_data": json.dumps({
                    "full_name": "Concurrent User",
                    "email": "arun.kumar@example.com",
                    "password": "Password123",
                    "phone": "9876543210",
                    "course": "MBA"
                }),
                "expected_result": "HTTP 409 Conflict: 'An account with this email address already exists.'",
                "actual_result": "",
                "status": "Not Executed",
                "defect_desc": ""
            },
            {
                "tc_id": f"TC-{code}-08",
                "req_code": code,
                "scenario": "Verify similar prefix email with different domain is accepted (arun.kumar@otherdomain.com)",
                "test_type": "Positive",
                "input_data": json.dumps({
                    "full_name": "Different Domain User",
                    "email": "arun.kumar@otherdomain.com",
                    "password": "Password123",
                    "phone": "9876543210",
                    "course": "MCA"
                }),
                "expected_result": "HTTP 201 Created: Registration successful.",
                "actual_result": "",
                "status": "Not Executed",
                "defect_desc": ""
            }
        ]

    # 4. Authentication / Login (keywords login, auth, credential)
    elif "login" in combined or "auth" in combined or "credential" in combined:
        return [
            {
                "tc_id": f"TC-{code}-01",
                "req_code": code,
                "scenario": "Verify successful user login with valid registered email and password",
                "test_type": "Positive",
                "input_data": json.dumps({"email": "arun.kumar@example.com", "password": "Password123"}),
                "expected_result": "HTTP 200 OK: Authentication successful. Session token granted.",
                "actual_result": "", "status": "Not Executed", "defect_desc": ""
            },
            {
                "tc_id": f"TC-{code}-02",
                "req_code": code,
                "scenario": "Verify login rejection with incorrect password",
                "test_type": "Negative",
                "input_data": json.dumps({"email": "arun.kumar@example.com", "password": "WrongPassword999"}),
                "expected_result": "HTTP 401 Unauthorized: 'Invalid email or password.'",
                "actual_result": "", "status": "Not Executed", "defect_desc": ""
            },
            {
                "tc_id": f"TC-{code}-03",
                "req_code": code,
                "scenario": "Verify login rejection for unregistered email address",
                "test_type": "Negative",
                "input_data": json.dumps({"email": "nonexistent@example.com", "password": "Password123"}),
                "expected_result": "HTTP 401 Unauthorized: 'Invalid email or password.'",
                "actual_result": "", "status": "Not Executed", "defect_desc": ""
            },
            {
                "tc_id": f"TC-{code}-04",
                "req_code": code,
                "scenario": "Verify login validation when credentials are submitted blank",
                "test_type": "Negative",
                "input_data": json.dumps({"email": "", "password": ""}),
                "expected_result": "HTTP 400 Bad Request: 'Email and password are required.'",
                "actual_result": "", "status": "Not Executed", "defect_desc": ""
            },
            {
                "tc_id": f"TC-{code}-05",
                "req_code": code,
                "scenario": "Verify protection against SQL Injection login bypass (' OR '1'='1)",
                "test_type": "Security",
                "input_data": json.dumps({"email": "' OR '1'='1' --", "password": "' OR '1'='1"}),
                "expected_result": "HTTP 400 Bad Request: Parameterized query prevents injection.",
                "actual_result": "", "status": "Not Executed", "defect_desc": ""
            },
            {
                "tc_id": f"TC-{code}-06",
                "req_code": code,
                "scenario": "Verify password boundary minimum length validation during credential entry",
                "test_type": "Boundary",
                "input_data": json.dumps({"email": "arun.kumar@example.com", "password": "Short"}),
                "expected_result": "HTTP 400 Bad Request: 'Password must be at least 8 characters.'",
                "actual_result": "", "status": "Not Executed", "defect_desc": ""
            },
            {
                "tc_id": f"TC-{code}-07",
                "req_code": code,
                "scenario": "Verify account lockout behavior after 5 consecutive failed login attempts",
                "test_type": "Security",
                "input_data": json.dumps({"email": "arun.kumar@example.com", "failed_attempts": 5}),
                "expected_result": "HTTP 429 Too Many Requests: 'Account temporarily locked. Retry after 15 minutes.'",
                "actual_result": "", "status": "Not Executed", "defect_desc": ""
            },
            {
                "tc_id": f"TC-{code}-08",
                "req_code": code,
                "scenario": "Verify session invalidation and token destruction upon user logout",
                "test_type": "Positive",
                "input_data": json.dumps({"session_token": "valid_active_token_xyz"}),
                "expected_result": "HTTP 200 OK: User logged out successfully.",
                "actual_result": "", "status": "Not Executed", "defect_desc": ""
            }
        ]

    # 5. Generic / Tailored Custom Requirement (At least 8 diverse test cases)
    safe_code = re.sub(r'[^A-Za-z0-9]', '', code) or "GEN"
    return [
        {
            "tc_id": f"TC-{safe_code}-01",
            "req_code": code,
            "scenario": f"Verify standard positive execution workflow for {req_title}",
            "test_type": "Positive",
            "input_data": json.dumps({
                "action": f"Execute {req_title}",
                "full_name": "Priya Sharma",
                "email": "priya.sharma@example.com",
                "password": "SecurePass123",
                "phone": "9812345678",
                "course": "MCA"
            }),
            "expected_result": f"HTTP 200/201: '{req_title}' processed successfully with valid parameters.",
            "actual_result": "", "status": "Not Executed", "defect_desc": ""
        },
        {
            "tc_id": f"TC-{safe_code}-02",
            "req_code": code,
            "scenario": f"Verify validation response for {req_title} when mandatory inputs are omitted",
            "test_type": "Negative",
            "input_data": json.dumps({
                "action": f"Execute {req_title}",
                "full_name": "",
                "email": "",
                "password": "",
                "phone": "",
                "course": ""
            }),
            "expected_result": "HTTP 400 Bad Request: Missing mandatory required parameters.",
            "actual_result": "", "status": "Not Executed", "defect_desc": ""
        },
        {
            "tc_id": f"TC-{safe_code}-03",
            "req_code": code,
            "scenario": f"Verify input format validation error handling for {req_title}",
            "test_type": "Negative",
            "input_data": json.dumps({
                "action": f"Execute {req_title}",
                "email": "invalid_email_format",
                "phone": "12345"
            }),
            "expected_result": "HTTP 400 Bad Request: Input format violation caught by validation parser.",
            "actual_result": "", "status": "Not Executed", "defect_desc": ""
        },
        {
            "tc_id": f"TC-{safe_code}-04",
            "req_code": code,
            "scenario": f"Verify minimum valid boundary threshold for {req_title}",
            "test_type": "Boundary",
            "input_data": json.dumps({
                "action": f"Execute {req_title}",
                "full_name": "Al",
                "password": "Password1"
            }),
            "expected_result": "HTTP 200/201: System accepts minimum boundary values.",
            "actual_result": "", "status": "Not Executed", "defect_desc": ""
        },
        {
            "tc_id": f"TC-{safe_code}-05",
            "req_code": code,
            "scenario": f"Verify maximum boundary limit enforcement for {req_title}",
            "test_type": "Boundary",
            "input_data": json.dumps({
                "action": f"Execute {req_title}",
                "full_name": "A" * 51,
                "boundary_check": "Exceeds maximum allowable field length"
            }),
            "expected_result": "HTTP 400 Bad Request: System cleanly blocks values exceeding maximum boundary.",
            "actual_result": "", "status": "Not Executed", "defect_desc": ""
        },
        {
            "tc_id": f"TC-{safe_code}-06",
            "req_code": code,
            "scenario": f"Verify duplicate collision and integrity handling for {req_title}",
            "test_type": "Security",
            "input_data": json.dumps({
                "action": f"Execute {req_title}",
                "email": "arun.kumar@example.com",
                "duplicate_attempt": True
            }),
            "expected_result": "HTTP 409 Conflict: System rejects duplicate record entry.",
            "actual_result": "", "status": "Not Executed", "defect_desc": ""
        },
        {
            "tc_id": f"TC-{safe_code}-07",
            "req_code": code,
            "scenario": f"Verify sanitization against malicious script/injection payload in {req_title}",
            "test_type": "Security",
            "input_data": json.dumps({
                "action": f"Execute {req_title}",
                "full_name": "<script>alert('XSS')</script>",
                "course": "MCA"
            }),
            "expected_result": "HTTP 400 Bad Request: Malicious payload rejected or sanitized.",
            "actual_result": "", "status": "Not Executed", "defect_desc": ""
        },
        {
            "tc_id": f"TC-{safe_code}-08",
            "req_code": code,
            "scenario": f"Verify graceful system recovery and rollback upon invalid state in {req_title}",
            "test_type": "Negative",
            "input_data": json.dumps({
                "action": f"Execute {req_title}",
                "state": "Simulate partial transaction failure"
            }),
            "expected_result": "HTTP 400/422: System maintains database consistency without crashes.",
            "actual_result": "", "status": "Not Executed", "defect_desc": ""
        }
    ]
