# Warmzone Hoodie

## Steps to run mouse.py:
Set up a virtual environment:
- python -m venv venv

Activate virtual environment:
- venv\Scripts\activate

Install necessary libraries:
- pip install pynput numpy pyinstaller
  
Save the mouse.py file and run this to create .exe file:
- pyinstaller --onefile mouse.py
  
Go to dist\mouse.exe and run it.
