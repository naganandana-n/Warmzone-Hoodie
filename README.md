# Warmzone Hoodie

## Steps to run mouse.py:
Set up a virtual environment:
- `python -m venv venv`

Activate virtual environment:
- `venv\Scripts\activate`

Install necessary libraries:
- `pip install pynput numpy pyinstaller`
  
Save the mouse.py file and run this to create .exe file:
- `pyinstaller --onefile mouse.py`
  
Go to `dist\mouse.exe` and run it.

## Steps to run audio.py:
Install necessary libraries:
- `pip install pipwin`
- `pipwin install pyaudio`
- `pip install numpy`

Save the audio.py file and run the program:
- `python audio.py`
  
Play music or system audio, and you should see live intensity values from 0 to 5.

To create the .exe file:
- `pyinstaller --onefile audio.py`

Go to `dist\audio.exe` and run it.
