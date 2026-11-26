@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Python nao encontrado. Instale o Python 3.10+ em https://www.python.org/downloads/ marcando "Add to PATH".
  pause
  exit /b 1
)
if not exist bovinus.db (
  echo Criando banco com dados simulados...
  py seed.py
)
start "" http://127.0.0.1:8000/dashboard
py app.py
pause
