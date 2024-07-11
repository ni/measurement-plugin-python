@echo off
REM The discovery service uses this script to install the dependencies
REM for the measurement service. You can customize this script for your
REM Python setup.

poetry install --only main
