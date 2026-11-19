@echo off
REM ============================================================
REM  IT-aanhuis Helpdesk AI - Windows starter
REM ============================================================
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    py it_aanhuis.py %*
) else (
    python it_aanhuis.py %*
)
endlocal
