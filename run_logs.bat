@echo off
cd /d %~dp0
powershell -ExecutionPolicy Bypass -File export_claude_log.ps1
pause
