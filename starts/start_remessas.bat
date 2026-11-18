@echo off
title VOXI - ENVIO DE REMESSAS
cd /d "%~dp0\.."
set PYTHONPATH=%cd%
set "PYTHON_EXE=python"
if exist "%cd%\venv\Scripts\python.exe" set "PYTHON_EXE=%cd%\venv\Scripts\python.exe"
if exist "%cd%\.venv\Scripts\python.exe" set "PYTHON_EXE=%cd%\.venv\Scripts\python.exe"
"%PYTHON_EXE%" -m scripts.executar_remessas
exit /b %errorlevel%
