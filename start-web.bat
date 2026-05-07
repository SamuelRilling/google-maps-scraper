@echo off
cd /d "%~dp0"
if not exist gmapsdata mkdir gmapsdata
start "Google Maps Scraper" google-maps-scraper.exe -web -data-folder gmapsdata
timeout /t 3 /nobreak >nul
start http://localhost:8080
