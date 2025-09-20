import sys
from src.actions import tap_on
from src.vision import detect_buttons
from src.device import take_screenshot

if __name__ == "__main__":
    if len(sys.argv) > 1:
        label = sys.argv[1]
        tap_on(label)
    else:
        # Debug mode: just show detected buttons
        take_screenshot()
        buttons = detect_buttons()
        print("Detected buttons:", buttons)