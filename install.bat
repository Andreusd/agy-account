@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo   Installing agy-account CLI Shim for Antigravity
echo ===================================================

:: Determine repository path
set SCRIPT_DIR=%~dp0
set TARGET_SCRIPT=%SCRIPT_DIR%agy_account.py

if not exist "%TARGET_SCRIPT%" (
    echo [ERROR] Could not find agy_account.py in %SCRIPT_DIR%
    exit /b 1
)

:: Find agy bin directory or fallback to local appdata
set AGY_BIN=%LOCALAPPDATA%\agy\bin

if not exist "%AGY_BIN%" (
    mkdir "%AGY_BIN%" 2>nul
)

:: Create the shim batch file
set SHIM_FILE=%AGY_BIN%\agy-account.bat

(
echo @echo off
echo python "%TARGET_SCRIPT%" %%*
) > "%SHIM_FILE%"

echo.
echo [SUCCESS] Shim successfully created at:
echo   %SHIM_FILE%
echo.
echo It points to:
echo   %TARGET_SCRIPT%
echo.
echo You can now use 'agy-account' from any terminal!
echo ===================================================
