@echo off
setlocal

docker compose up --build -d
if errorlevel 1 exit /b %errorlevel%
echo Project Management MVP is running at http://localhost:8000
