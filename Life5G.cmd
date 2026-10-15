@echo off
setlocal DisableDelayedExpansion
chcp 65001 >nul
set "PYTHONUTF8=1"
cd /d "%~dp0"
if errorlevel 1 exit /b 1
set "LIFE_PY="
set "LIFE_CHECK=import sys; assert sys.version_info >= (3,11) and sys.maxsize > 2**32"
rem Never ask py.exe for a specific version: the Python install manager (py install)
rem reports a missing version on the console and may stop this script.
call py -c "%LIFE_CHECK%" >nul 2>&1
if not errorlevel 1 (
    set "LIFE_PY=py"
    goto run
)
call python -c "%LIFE_CHECK%" >nul 2>&1
if not errorlevel 1 (
    set "LIFE_PY=python"
    goto run
)
echo Не найден Python 3.11 или новее, x64. Установите его: https://www.python.org/downloads/windows/
set "LIFE_STATUS=1"
goto finish
:run
%LIFE_PY% -u life5g.py %*
set "LIFE_STATUS=%ERRORLEVEL%"
:finish
if not "%LIFE_STATUS%"=="0" if "%~1"=="" pause
exit /b %LIFE_STATUS%
