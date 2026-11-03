@echo off
title JKLU SmartSchedule Dashboard
echo Starting JKLU SmartSchedule Dashboard...
py -m streamlit run streamlit_app.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo Streamlit failed to start. Trying python instead...
    python -m streamlit run streamlit_app.py
)
if %ERRORLEVEL% neq 0 (
    echo.
    echo Failed to start Streamlit. Please make sure Python and Streamlit are installed.
    pause
)
