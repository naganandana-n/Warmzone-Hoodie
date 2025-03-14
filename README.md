# Warmzone Hoodie

## Table of Contents
- [Steps to run mouse.py](#steps-to-run-mousepy)
- [Steps to run screen.py](#steps-to-run-screenpy)
- [Steps to run screen2.py & screen-quadrants.py](#steps-to-run-screen2py--screen-quadrantspy)
- [Steps to run audio.py](#steps-to-run-audiopy)

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

## Steps to run screen.py:
Install necessary libraries:
- `pip install mss numpy pillow`

Save the screen.py file and run the program:
- `python screen.py`
  
As the colors on your screen change, the terminal will show: 
- Screen Color: RGB (120, 45, 200)

To create the .exe file:
- `pyinstaller --onefile screen.py`

Go to `dist\screen.exe` and run it.

## Steps to run screen2.py & screen-quadrants.py:
Install necessary libraries:
- `pip install mss numpy pillow`
- `pip install scikit-learn`

Save the screen2.py / screen-quadrants.py file and run the program:
- `python screen2.py`
- `python screen-quadrants.py`

screen2.py output: You should see the RGB codes of the top 5 dominant colors from the screen being displayed.
screen-quadrants.py output: You should see the dominant colors in each quadrant of the screen (to be displayed around the V).

## Steps to run audio.py & audio2.py:
Check if Stereo Mix is Enabled and Set as Default:
- Open Sound Settings (Win + R → mmsys.cpl → Enter)
- Go to the Recording tab.
- Find Stereo Mix.
- Right-click it and Enable.
- Click Set as Default Device.
- Click Apply → OK.
- Right-click Stereo Mix → Select Properties.
- Go to the Levels tab.
- Increase the volume to at least 50%.
- Click Apply → OK.

Install necessary libraries:
- `pip install sounddevice numpy pyinstaller`

Save the audio.py / audio2.py file and run the program:
- `python audio.py`
- `python audio2.py`
  
Play music or system audio, and you should see live intensity values from 0 to 5.

To create the .exe file:
- `pyinstaller --onefile audio.py`
  
Go to `dist\audio.exe` and run it.
