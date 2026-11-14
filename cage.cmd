@echo off
setlocal
set "PYTHONPATH=%~dp0src"
python -m rancage %*
exit /b %ERRORLEVEL%
