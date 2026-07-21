@echo off
echo Building Bitburner Save Editor...
pip install -r requirements.txt pyinstaller
pyinstaller --onefile --windowed --name "BitburnerSaveEditor" ^
  --icon=assets/icon.ico ^
  --add-data "assets;assets" ^
  main.py
echo Done! Check dist/ folder.
pause
