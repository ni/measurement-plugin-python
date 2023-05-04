@echo off
REM The discovery service uses this script to start the measurement service.
REM You can customize this script for your Python setup. The -v option logs
REM messages with level INFO and above.

REM If you don't have NI Instrument Simulator v2.0 hardware, you can simulate 
REM it in software by adding the --use-simulation option to this command.
.venv\Scripts\python.exe measurement.py -v
