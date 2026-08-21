@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\pythonw.exe" (
    echo Ambiente virtual nao encontrado nesta pasta.
    echo Abra o PowerShell aqui e rode:
    echo   python -m venv .venv
    echo   .venv\Scripts\Activate.ps1
    echo   pip install -r requirements.txt
    echo Depois tente abrir este atalho de novo.
    pause
    exit /b 1
)

start "" ".venv\Scripts\pythonw.exe" "run_web.py"
