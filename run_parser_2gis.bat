@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Запуск Parser2GIS...
py -3 run_parser_2gis.py %* 2>nul || python run_parser_2gis.py %*
if errorlevel 1 pause
