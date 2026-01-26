@echo off
echo Restarting PostgreSQL service...
net stop postgresql-x64-18
timeout /t 2 /nobreak >nul
net start postgresql-x64-18
echo.
echo PostgreSQL restarted successfully!
echo.
echo Press any key to close...
pause >nul
