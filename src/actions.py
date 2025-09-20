from src.device import take_screenshot, tap
from src.vision import detect_buttons
from difflib import get_close_matches

def tap_on(label: str):
    """Find element by text label and tap on it."""
    # Take fresh screenshot + detect
    take_screenshot()
    buttons = detect_buttons()

    # Extract all detected labels
    detected_labels = [b["label"] for b in buttons]

    # Find closest match to the requested label
    match = get_close_matches(label, detected_labels, n=1, cutoff=0.6)

    if not match:
        raise ValueError(f"Could not find element with label close to '{label}'. Detected: {detected_labels}")

    chosen = match[0]
    element = next(b for b in buttons if b["label"] == chosen)

    # Compute center point for tap
    x_center = element["x"] + element["w"] // 2
    y_center = element["y"] + element["h"] // 2

    print(f"Tapping on '{chosen}' at ({x_center}, {y_center})")

    tap(x_center, y_center)