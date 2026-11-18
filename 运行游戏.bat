@echo off
chcp 65001 >nul
title Jade Hunter - Zhu Yu Ji
cd /d "%~dp0"
echo ============================================================
echo    Zhu Yu Ji / JADE HUNTER
echo ============================================================
echo.
set "PYEXE="
where py >nul 2>nul && set "PYEXE=py -3"
if not defined PYEXE (where python >nul 2>nul && set "PYEXE=python")
if not defined PYEXE (
  echo [ERROR] Python not found. Please install Python 3.8-3.12 first.
  echo         https://www.python.org/downloads/
  pause
  exit /b 1
)
%PYEXE% -c "import panda3d" >nul 2>nul
if errorlevel 1 (
  echo [INFO] Installing Panda3D, please wait...
  %PYEXE% -m pip install -r requirements.txt
)
echo [INFO] Starting game...
%PYEXE% demo_v23ext.py
if errorlevel 1 pause
