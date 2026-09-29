@echo off
title AgriTwin System Startup
color 0A

echo.
echo  ============================================================
echo      AGRITWIN SMART FARM — ONE-CLICK SYSTEM STARTUP
echo  ============================================================
echo.
echo  This script starts everything on the LAPTOP side.
echo  Pi services (MQTT, fog sync, camera) auto-run via systemd.
echo.

REM ─── Check project root ──────────────────────────────────────
set ROOT=%~dp0
set VENV=%ROOT%.venv\Scripts\python.exe

if not exist "%VENV%" (
    echo [ERROR] Virtual environment not found at .venv\
    echo         Run: python -m venv .venv ^&^& .venv\Scripts\pip install -r cloud\backend\requirements.txt
    pause
    exit /b 1
)

REM ─── 0. Verify Pi is reachable ───────────────────────────────
echo [0/4] Checking Pi connectivity...
ping -n 1 -w 2000 agritwin-fog.local >nul 2>&1
if %errorlevel%==0 (
    echo       Pi reachable at agritwin-fog.local
) else (
    echo       [WARN] Pi not reachable — ESP32 data and camera will not work
    echo              Make sure Pi is powered on and on the same WiFi
)
echo.

REM ─── 1. Ollama (AI assistant — optional, skips if not installed) ──
echo [1/4] Checking Ollama...

REM Try both system PATH and the default install location
set OLLAMA_EXE=
where ollama >nul 2>&1
if %errorlevel%==0 (
    set OLLAMA_EXE=ollama
) else if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" (
    set OLLAMA_EXE=%LOCALAPPDATA%\Programs\Ollama\ollama.exe
)

if defined OLLAMA_EXE (
    REM Check if Ollama is already running
    powershell -Command "try { (Invoke-WebRequest -Uri 'http://localhost:11434/api/tags' -UseBasicParsing -TimeoutSec 2).StatusCode } catch { exit 1 }" >nul 2>&1
    if %errorlevel%==0 (
        echo       Ollama already running on :11434
    ) else (
        echo       Starting Ollama (LLaMA 3)...
        start "Ollama LLaMA3" /MIN cmd /k "title Ollama LLaMA3 && \"%OLLAMA_EXE%\" serve"
        echo       Waiting for Ollama to be ready...
        timeout /t 8 /nobreak >nul
        REM Pull llama3 if not already downloaded
        "%OLLAMA_EXE%" list 2>nul | findstr "llama3" >nul 2>&1
        if %errorlevel%==1 (
            echo       Pulling llama3 model (first time — may take a while)...
            start "Ollama Pull" /WAIT cmd /c "\"%OLLAMA_EXE%\" pull llama3"
        )
        echo       Ollama started on :11434
    )
) else (
    echo       [SKIP] Ollama not installed — AI assistant disabled
    echo              Install from: https://ollama.com
)
echo.

REM ─── 2. Cloud Backend (FastAPI) ──────────────────────────────
echo [2/4] Starting Cloud Backend (port 8000)...
start "AgriTwin Backend" cmd /k "title AgriTwin Backend && cd /d %ROOT%cloud\backend && %VENV% -m uvicorn main_working:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 6 /nobreak >nul
echo       Backend started — http://localhost:8000
echo       API docs        — http://localhost:8000/docs
echo.

REM ─── 3. Frontend Dashboard (Next.js) ─────────────────────────
echo [3/4] Starting Dashboard (port 3000)...
start "AgriTwin Dashboard" cmd /k "title AgriTwin Dashboard && cd /d %ROOT%cloud\frontend && npm run dev"
timeout /t 5 /nobreak >nul
echo       Dashboard started — http://localhost:3000
echo       Camera page      — http://localhost:3000/camera
echo.

REM ─── 4. Flutter App (optional) ───────────────────────────────
echo [4/4] Flutter mobile app...
where flutter >nul 2>&1
if %errorlevel%==0 (
    echo       Detected ADB devices:
    adb devices -l 2>nul | findstr /v "List attached" | findstr /r /c:"device"
    echo.
    echo       [P] Deploy to Phone (wireless ADB)
    echo       [W] Run on Windows desktop
    echo       [N] Skip
    set /p FLUTTER_TARGET="       Choose [P/W/N]: "
    if /i "%FLUTTER_TARGET%"=="p" (
        start "AgriTwin Flutter" cmd /k "title AgriTwin Flutter && cd /d %ROOT%mobile && flutter run"
        echo       Flutter deploying to phone via wireless debug...
    ) else if /i "%FLUTTER_TARGET%"=="w" (
        start "AgriTwin Flutter" cmd /k "title AgriTwin Flutter && cd /d %ROOT%mobile && flutter run -d windows"
        echo       Flutter app launching on Windows...
    ) else (
        echo       Skipped. Run manually: cd mobile ^&^& flutter run
    )
) else (
    echo       [SKIP] Flutter SDK not in PATH
)
echo.

REM ─── 5. ESP32 Firmware Upload (optional) ─────────────────────
echo [5] ESP32 firmware upload...
echo       Detected COM ports:
wmic path Win32_PnPEntity where "Name like '%%COM%%'" get Name 2>nul | findstr "COM"
echo.
set /p UPLOAD_FW="       Upload firmware to ESP32? [y/N]: "
if /i "%UPLOAD_FW%"=="y" (
    start "ESP32 Upload" cmd /k "title ESP32 Firmware Upload && cd /d %ROOT%edge && C:\Users\aml\.platformio\penv\Scripts\platformio.exe run --target upload && echo. && echo Firmware uploaded! Press any key to close. && pause"
    echo       Firmware upload started in new window...
)
echo.

REM ─── Summary ─────────────────────────────────────────────────
echo  ============================================================
echo      SYSTEM STARTED — OPEN THESE IN YOUR BROWSER
echo  ============================================================
echo.
echo      Dashboard   :  http://localhost:3000
echo      DT Brain    :  http://localhost:3000/dt-brain
echo      Camera page :  http://localhost:3000/camera
echo      API docs    :  http://localhost:8000/docs
echo      Metrics     :  http://localhost:8000/metrics
echo      Health      :  http://localhost:8000/health
echo.
echo  ─── Network (home Wi-Fi) ────────────────────────
echo      Laptop      :  192.168.1.4
echo      Pi (fog)    :  192.168.1.7  (agritwin-fog.local)
echo      ESP32       :  USB — mDNS resolves Pi automatically
echo      Phone       :  Wireless ADB connected
echo.
echo  ─── Pi status (run in a separate terminal) ──────────────
echo      ssh pi@agritwin-fog.local -p 22               (pw: pi123456)
echo      sudo systemctl status agritwin-fog.service camera.service
echo.
echo  ─── Data flow ───────────────────────────────────────────
echo      ESP32 → Pi MQTT → Pi InfluxDB → Cloud Backend → Dashboard
echo      Pi Camera (auto every 5 min) → Cloud → /camera page
echo.
echo  Press any key to open the dashboard in a browser...
pause >nul
start http://localhost:3000
