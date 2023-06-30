@echo off
REM The discovery service uses this script to start the measurement service.
REM You can customize this script for your Python setup. The -v option logs
REM messages with level INFO and above.

call python "%~dp0measurement.py" -v
