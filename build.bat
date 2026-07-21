@echo off
echo Building Supermarket Save Editor...
pip install -r requirements.txt pyinstaller
pyinstaller --onefile --windowed --name "SupermarketSaveEditor" ^
  --icon=assets/icon.ico ^
  --add-data "assets;assets" ^
  main.py
echo Done! Check dist/ folder.
pause
