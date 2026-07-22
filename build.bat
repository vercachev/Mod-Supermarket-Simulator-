@echo off
echo Building Supermarket Together Save Editor...
pip install -r requirements.txt pyinstaller
pyinstaller --onefile --windowed --name "SupermarketTogetherSaveEditor" ^
  --icon=assets/icon.ico ^
  --add-data "assets;assets" ^
  main.py
echo Done! Check dist/
pause
