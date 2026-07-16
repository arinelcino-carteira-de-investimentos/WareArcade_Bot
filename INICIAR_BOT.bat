@echo off
chcp 65001 >nul
title WareArcadeBot
color 0A

echo.
echo ============================================================
echo   WareArcadeBot - Instalacao e Inicio (modo automatico)
echo ============================================================
echo.

cd /d "%~dp0"
echo Pasta: %cd%
echo.

REM Verifica python
where python >nul 2>nul
if %errorlevel%==0 (
    set PYEXE=python
    goto run
)
where py >nul 2>nul
if %errorlevel%==0 (
    set PYEXE=py
    goto run
)

color 0C
echo [ERRO] Python nao encontrado!
echo.
echo Baixe e instale o Python em: https://www.python.org/downloads/
echo IMPORTANTE: marque "Add Python to PATH" durante a instalacao.
echo.
pause
exit /b 1

:run
echo [OK] Python encontrado.
echo.
"%PYEXE%" "%~dp0instalar.py"

echo.
echo ============================================================
pause
