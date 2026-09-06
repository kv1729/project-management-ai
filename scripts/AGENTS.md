# Development Scripts

This directory contains platform-specific Docker Compose start and stop scripts for Windows PowerShell, Windows Command Prompt, macOS, and Linux.

The scripts expect Docker Desktop or Docker Engine with Compose v2 available on `PATH`. They should remain thin wrappers around `docker compose` and should not contain application logic or secrets.