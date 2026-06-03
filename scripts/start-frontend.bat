@echo off
setlocal

set PORT=5187

netstat -an | findstr ":%PORT% " | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo Port %PORT% already in use, assuming Vite is running.
    exit /b 0
)

set REPO_ROOT=%~dp0..
cd /d "%REPO_ROOT%"
echo Starting Vite dev server...
start "vite-dev" /min cmd /c "npm run dev:android"
echo Waiting for Vite to start...

set /a COUNT=0
:WAIT_LOOP
timeout /t 1 /nobreak >nul
netstat -an | findstr ":%PORT% " | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo Vite dev server is ready.
    exit /b 0
)
set /a COUNT+=1
if %COUNT% lss 30 goto WAIT_LOOP

echo Timeout waiting for Vite to start.
exit /b 1
