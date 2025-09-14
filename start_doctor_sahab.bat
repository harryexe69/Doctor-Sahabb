@echo off
echo 🏥 Doctor Sahab - Complete Health Assistant
echo ==========================================
echo.

echo 🚀 Starting Backend Server...
start "Doctor Sahab Backend" cmd /k "python doctor_sahab_standalone.py"

echo.
echo ⏳ Waiting for backend to start...
timeout /t 3 /nobreak >nul

echo.
echo 🌐 Opening Frontend in Browser...
start "" "doctor_sahab_frontend.html"

echo.
echo ✅ Doctor Sahab is now running!
echo.
echo 📍 Backend: http://localhost:8000
echo 🌐 Frontend: doctor_sahab_frontend.html
echo.
echo 🛑 To stop: Close the backend command window
echo.
pause


