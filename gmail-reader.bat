@echo off
rem Windows launcher for gmail-reader: run gmail_reader.py with the local venv.
"%~dp0.venv\Scripts\python.exe" "%~dp0gmail_reader.py" %*
