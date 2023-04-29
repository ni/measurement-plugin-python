@echo off
REM The discovery service uses this script to start the measurement service.
REM You can customize this script for your Python setup. The -v option logs
REM messages with level INFO and above.

.venv\Scripts\nidcpower_source_dc_voltage -v
