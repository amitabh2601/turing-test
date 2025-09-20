import subprocess
from src.vision import detect_buttons  # Your OCR + button detection
from src.device import take_screenshot
from difflib import get_close_matches
import time

# -------------------
# Adapters unchanged
# -------------------
class AndroidAdapter:
    def __init__(self, device_id="emulator-5554"):
        self.device_id = device_id

    def install_app(self, apk_path):
        subprocess.run(["adb", "-s", self.device_id, "install", "-r", apk_path], check=True)

    def uninstall_app(self, package_name):
        subprocess.run(["adb", "-s", self.device_id, "uninstall", package_name], check=True)

    def launch_app(self, package_name):
        subprocess.run([
            "adb", "-s", self.device_id, "shell", "monkey",
            "-p", package_name,
            "-c", "android.intent.category.LAUNCHER", "1"
        ], check=True)

    def tap(self, x, y):
        subprocess.run(["adb", "-s", self.device_id, "shell", "input", "tap", str(x), str(y)], check=True)

    def enter_text(self, x, y, text):
        self.tap(x, y)
        subprocess.run(["adb", "-s", self.device_id, "shell", "input", "text", text.replace(" ", "%s")], check=True)


class IOSAdapter:
    def __init__(self, simulator_id="booted"):
        self.simulator_id = simulator_id

    def install_app(self, app_path):
        subprocess.run(["xcrun", "simctl", "install", self.simulator_id, app_path], check=True)

    def uninstall_app(self, bundle_id):
        subprocess.run(["xcrun", "simctl", "uninstall", self.simulator_id, bundle_id], check=True)

    def launch_app(self, bundle_id):
        subprocess.run(["xcrun", "simctl", "launch", self.simulator_id, bundle_id], check=True)

    def tap(self, x, y):
        # TODO: implement iOS tap via simctl or helper agent
        pass

    def enter_text(self, x, y, text):
        # TODO: implement iOS enter text
        pass

# -------------------
# Helper to merge adjacent OCR boxes
# -------------------
def merge_adjacent_buttons(buttons, max_horizontal_gap=20, max_vertical_gap=15):
    """
    Merge OCR boxes that are close together horizontally or vertically
    """
    if not buttons:
        return []

    # Sort top-to-bottom, left-to-right
    buttons = sorted(buttons, key=lambda b: (b['y'], b['x']))
    merged = []
    current = buttons[0]

    for b in buttons[1:]:
        same_line = abs(b['y'] - current['y']) <= max_vertical_gap
        close_horizontally = (b['x'] - (current['x'] + current['w'])) <= max_horizontal_gap
        close_vertically = (b['y'] - (current['y'] + current['h'])) <= max_vertical_gap

        if (same_line and close_horizontally) or close_vertically:
            # Merge labels
            current['label'] += " " + b['label']
            # Expand width and height
            current['w'] = max(current['x'] + current['w'], b['x'] + b['w']) - current['x']
            current['h'] = max(current['h'], b['y'] + b['h'] - current['y'])
        else:
            merged.append(current)
            current = b

    merged.append(current)
    return merged

# -------------------
# Main Device Class
# -------------------
class TuringTestDevice:
    def __init__(self, platform_name, device_id=None):
        self.platform_name = platform_name.lower()
        if self.platform_name == "android":
            self.adapter = AndroidAdapter(device_id=device_id or "emulator-5554")
        elif self.platform_name == "ios":
            self.adapter = IOSAdapter(simulator_id=device_id or "booted")
        else:
            raise ValueError(f"Unsupported platform: {platform_name}")

    def install_app(self, app_path_or_apk):
        self.adapter.install_app(app_path_or_apk)

    def uninstall_app(self, package_or_bundle_id):
        self.adapter.uninstall_app(package_or_bundle_id)

    def launch_app(self, package_or_bundle_id):
        self.adapter.launch_app(package_or_bundle_id)

    def tap(self, x, y):
        self.adapter.tap(x, y)

    def enter_text(self, x, y, text):
        self.adapter.enter_text(x, y, text)

    # -------------------
    # Locator-free methods
    # -------------------

    def words_match(self, label, ocr_text, threshold=0.6):
        """
        Returns True if enough words in label appear in ocr_text.
        """
        label_words = set(label.lower().split())
        ocr_words = set(ocr_text.lower().split())
        matches = label_words & ocr_words
        return len(matches) / len(label_words) >= threshold

    def tap_on(self, label, confidence_threshold=0.6, timeout=5, interval=0.5):
        """
        Tap on a button detected by OCR that best matches the label.
        Waits until the button appears or timeout.
        """
        end_time = time.time() + timeout
        label_lower = label.lower()

        while time.time() < end_time:
            take_screenshot()
            buttons = merge_adjacent_buttons(detect_buttons())
            # Debug logs
            print("Detected buttons:", [b['label'] for b in buttons])

            button_labels_lower = [b['label'].lower() for b in buttons]
            matches = get_close_matches(label_lower, button_labels_lower, n=1, cutoff=confidence_threshold)

            if matches:
                button = next(b for b in buttons if b['label'].lower() == matches[0])
                x = button['x'] + button['w'] // 2
                y = button['y'] + button['h'] // 2
                print(f"Tapping on '{button['label']}' at ({x},{y})")
                self.tap(x, y)
                return

            time.sleep(interval)

        raise ValueError(f"No button found matching '{label}' after {timeout} seconds")

    def enter_text_on(self, label, text, threshold=0.6, timeout=5, interval=0.5):
        """
        Find input field by label and enter text.
        Uses word-level fuzzy matching to handle OCR misreads or word order issues.
        Waits until the field appears or timeout.
        """
        end_time = time.time() + timeout
        while time.time() < end_time:
            take_screenshot()
            buttons = detect_buttons()  # OCR + bounding boxes

            # Debug logs
            print("Detected OCR boxes:")
            for b in buttons:
                print(f"  '{b['label']}' at ({b['x']},{b['y']},{b['w']},{b['h']})")

            buttons = merge_adjacent_buttons(detect_buttons())  # Merge boxes first
            # Debug log
            print("Merged OCR boxes:", [b['label'] for b in buttons])

            # Word-level matching
            matches = [b for b in buttons if self.words_match(label, b['label'], threshold)]
            if matches:
                field = matches[0]
                x = field['x'] + field['w'] // 2
                y = field['y'] + field['h'] // 2
                print(f"Entering text '{text}' into '{field['label']}' at ({x},{y})")
                self.enter_text(x, y, text)
                return

            time.sleep(interval)

        raise ValueError(f"No input field found matching '{label}' after {timeout} seconds")