from src.turing_test_device import TuringTestDevice

device = TuringTestDevice("android", device_id="emulator-5554")
device.launch_app("com.google.android.gm")  # Gmail

# Locator-free actions
device.tap_on("Got It")
device.tap_on("Add an email address")
device.tap_on("Google")
device.enter_text_on("Email or phone", "friend@example.com")
device.tap_on("Next", timeout=10, interval=0.5)
