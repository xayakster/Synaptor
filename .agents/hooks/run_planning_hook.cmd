@echo off
set "HOOK_DIR=%~dp0"
python "%HOOK_DIR%planning_hook.py" %*
exit /b %ERRORLEVEL%
