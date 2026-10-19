"""
Input Validation Module for Student Registration Portal
Provides strict server-side validation rules and meaningful error messages.
"""
import re

VALID_COURSES = [
    "MCA",
    "M.Tech",
    "B.Tech",
    "MBA",
    "M.Sc Computer Science"
]

# Explicit Boundary and Validation Constants
MIN_NAME_LENGTH = 2
MAX_NAME_LENGTH = 50
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 64
PHONE_LENGTH = 10

# Regex Patterns
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
NAME_REGEX = re.compile(r"^[a-zA-Z\s]+$")
PHONE_REGEX = re.compile(r"^\d{10}$")


def validate_student_registration(data):
    """
    Validates student registration input data.
    
    Returns:
        tuple: (is_valid: bool, errors: dict)
    """
    errors = {}
    
    if not isinstance(data, dict):
        return False, {"general": "Invalid request payload format. JSON object expected."}

    # Extract and sanitize fields
    full_name = str(data.get("full_name", "")).strip()
    email = str(data.get("email", "")).strip()
    password = str(data.get("password", ""))  # Don't strip password to preserve user spaces if intended
    phone = str(data.get("phone", "")).strip()
    course = str(data.get("course", "")).strip()

    # 1. Full Name Validation
    if not full_name:
        errors["full_name"] = "Full name is required."
    elif len(full_name) < MIN_NAME_LENGTH:
        errors["full_name"] = f"Full name must be at least {MIN_NAME_LENGTH} characters."
    elif len(full_name) > MAX_NAME_LENGTH:
        errors["full_name"] = f"Full name cannot exceed {MAX_NAME_LENGTH} characters."
    elif not NAME_REGEX.match(full_name):
        errors["full_name"] = "Full name must contain only alphabets and spaces."

    # 2. Email Validation
    if not email:
        errors["email"] = "Email address is required."
    elif not EMAIL_REGEX.match(email):
        errors["email"] = "Invalid email format. Expected format: user@domain.com."

    # 3. Password Validation
    if not password:
        errors["password"] = "Password is required."
    elif len(password) < MIN_PASSWORD_LENGTH:
        errors["password"] = f"Password must be at least {MIN_PASSWORD_LENGTH} characters long."
    elif len(password) > MAX_PASSWORD_LENGTH:
        errors["password"] = f"Password cannot exceed {MAX_PASSWORD_LENGTH} characters."
    elif not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
        errors["password"] = "Password must contain at least one letter and one number."

    # 4. Phone Number Validation
    if not phone:
        errors["phone"] = "Phone number is required."
    elif not PHONE_REGEX.match(phone):
        errors["phone"] = f"Phone number must be exactly {PHONE_LENGTH} numeric digits."

    # 5. Course Validation
    if not course:
        errors["course"] = "Course selection is required."
    elif course not in VALID_COURSES:
        errors["course"] = f"Course must be one of: {', '.join(VALID_COURSES)}."

    is_valid = len(errors) == 0
    return is_valid, errors
