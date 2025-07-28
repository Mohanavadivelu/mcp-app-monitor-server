@echo off
REM Windows batch script to clean up Python cache files
REM This is a simple wrapper around the Python cleanup script

echo MCP Application Monitor Server - Cleanup Script
echo ==================================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python or add it to your PATH
    pause
    exit /b 1
)

REM Run the Python cleanup script with all arguments passed through
python "%~dp0cleanup.py" %*

REM Pause to see results if run by double-clicking
if "%1"=="" pause
