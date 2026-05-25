@echo off
title Servidor HR XML Processor
echo Iniciando el servidor Flask utilizando el entorno virtual (.venv)...
echo.
if not exist .venv\Scripts\python.exe (
    echo [ERROR] No se encontro el entorno virtual en la carpeta .venv.
    echo Asegurate de crearlo primero ejecutando: python -m venv .venv
    echo.
    pause
    exit /b
)
.venv\Scripts\python.exe app.py
pause
