# Pastel Pocket Claw

A tiny virtual claw machine game written in Python with Tkinter. Collect the
soft, colorful prizes and see how many you can deliver to the chute.

## Install

1. Install Python 3.10 or newer from [python.org](https://www.python.org/downloads/).
   On Windows, enable **Add Python to PATH** in the installer.
2. Download or clone this project, then open a terminal in the `python_game`
   folder (the folder containing `main.py`).
3. Check that Python is available:

   ```bash
   python --version
   ```

   On macOS or Linux, use `python3 --version` if `python` is not recognized.
4. Check Tkinter by running `python -m tkinter` (or `python3 -m tkinter`). A
   small Tk window should appear. Close it to continue. Tkinter is included in
   most Python installers and no other packages are needed.

If the Tkinter check fails on Debian or Ubuntu, install it with
`sudo apt install python3-tk`. On macOS, use the official python.org installer
if your Python distribution does not include Tkinter. On Windows, rerun the
Python installer and ensure **Tcl/Tk and IDLE** is selected.

## Run

From the `python_game` folder, launch the game:

```bash
python main.py
```

If your system uses `python3`, run `python3 main.py` instead. The game opens in
a window; keep the terminal open while playing.

## Controls

- **Left / Right arrows**: move the claw while it is at the top
- **Space**: lower the claw and try to grab the nearest prize
- **R**: start a fresh game

Each prize delivered to the chute adds one point to your score.
