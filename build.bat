@echo off
echo Building Danny Capture...
py -m pip install pyinstaller
py -m PyInstaller --name "DannyCapture" --windowed --onefile --icon="icon.ico" main.py
echo Build Complete! Check the 'dist' folder.
pause
