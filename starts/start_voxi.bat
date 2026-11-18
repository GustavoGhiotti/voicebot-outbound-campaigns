@echo off
setlocal
title Envio Ativo VOXI

cd /d "%~dp0.."
set "PYTHONPATH=%cd%"
set "PYTHON_EXE=python"
if exist "%cd%\venv\Scripts\python.exe" set "PYTHON_EXE=%cd%\venv\Scripts\python.exe"
if exist "%cd%\.venv\Scripts\python.exe" set "PYTHON_EXE=%cd%\.venv\Scripts\python.exe"

echo =====================================
if "%~1"=="" (
    echo Iniciando VOXI - todas as carteiras
) else (
    echo Iniciando VOXI - argumentos: %*
)
echo =====================================

rem  Sem argumento      -> todas as carteiras (padrao do runner)
rem  1o arg sem "-"      -> atalho de carteira: start_voxi.bat zeta  =  --carteira zeta
rem  1o arg comecando "-" -> repassa as flags direto: start_voxi.bat --dry-run --debug
if "%~1"=="" goto :todas
set "PRIMEIRO=%~1"
if "%PRIMEIRO:~0,1%"=="-" goto :flags
goto :carteira

:todas
"%PYTHON_EXE%" -m scripts.executar_voxi
goto :fim

:carteira
"%PYTHON_EXE%" -m scripts.executar_voxi --carteira %*
goto :fim

:flags
"%PYTHON_EXE%" -m scripts.executar_voxi %*
goto :fim

:fim
set "CODIGO_SAIDA=%errorlevel%"
echo.
echo =====================================
if "%CODIGO_SAIDA%"=="0" (
    echo VOXI concluido com sucesso!
) else (
    echo VOXI finalizado com erro %CODIGO_SAIDA%.
)
echo =====================================
exit /b %CODIGO_SAIDA%
