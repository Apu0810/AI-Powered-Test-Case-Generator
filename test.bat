@echo off
echo ======================================================================
echo  Running Automated Test Suite (Pytest / Unittest)
echo ======================================================================
echo.

IF EXIST venv\Scripts\pytest.exe (
    echo [*] Running tests with Pytest...
    venv\Scripts\pytest.exe -v
) ELSE (
    echo [*] Running tests with Python unittest...
    python -m unittest discover tests -v
)

echo.
pause
