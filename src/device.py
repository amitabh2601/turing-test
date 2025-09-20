import os

def take_screenshot(filename="screen.png"):
    os.system(f"adb exec-out screencap -p > {filename}")

def tap(x, y):
    os.system(f"adb shell input tap {x} {y}")