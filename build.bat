@echo off
REM AI Video GUI Build Script (Full Package with Installer)
REM 1. PyInstaller builds the exe
REM 2. Inno Setup generates the installer

setlocal

echo ========================================
echo AiVideoGUI Build Tool
echo ========================================
echo.

REM Check if Inno Setup is installed
set "INNO_SETUP=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist "%INNO_SETUP%" (
    echo [ERROR] Inno Setup not found
    echo Download from: https://jrsoftware.org/isdl.php
    pause
    exit /b 1
)

echo [1/5] Syncing version number...
powershell -ExecutionPolicy Bypass -File update_version.ps1
if errorlevel 1 (
    echo [ERROR] Failed to sync version
    pause
    exit /b 1
)
echo Version synced
echo.

echo [2/5] Cleaning old build files...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist output rmdir /s /q output
echo Clean completed
echo.

echo [3/5] Running PyInstaller...
uv run pyinstaller --clean -y ai-video-gui.spec
if errorlevel 1 (
    echo [ERROR] PyInstaller failed
    pause
    exit /b 1
)
echo PyInstaller completed
echo.

echo [4/5] Generating installer...
"%INNO_SETUP%" installer.iss
if errorlevel 1 (
    echo [ERROR] Inno Setup failed
    pause
    exit /b 1
)
echo Installer generated
echo.

echo [5/5] Build completed!
echo.
echo Output files:
echo - EXE: dist\AiVideoGUI\AiVideoGUI.exe
echo - Installer: output\AiVideoGUI-Setup-*.exe
echo.
echo ========================================

REM Ask if open output directory
set /p open="Open output directory? (Y/N): "
if /i "%open%"=="Y" (
    start explorer output
)

endlocal
pause
