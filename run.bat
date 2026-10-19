@echo off
echo ======================================================================
echo  AI-Powered Requirements and Test Case Generator - Student Portal
echo  MCA Practical Lab Demonstration
echo ======================================================================
echo.

IF EXIST venv\Scripts\python.exe (
    echo [*] Starting Flask web server using virtual environment...
    echo [*] Access the application in your browser at: http://127.0.0.1:5000
    echo.
    venv\Scripts\python.exe app.py
) ELSE (
    echo [*] Starting Flask web server using system Python...
    echo [*] Access the application in your browser at: http://127.0.0.1:5000
    echo.
    python app.py
)

pause
