@echo off
echo Building Cookie Clicker Save Editor...
pip install -r requirements.txt pyinstaller
pyinstaller --onefile --windowed --name "CookieClickerSaveEditor" ^
  --icon=assets/icon.ico ^
  --add-data "assets;assets" ^
  main.py
echo Done! Check dist/
pause
