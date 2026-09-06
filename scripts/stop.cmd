@echo off
setlocal

docker compose down
exit /b %errorlevel%
