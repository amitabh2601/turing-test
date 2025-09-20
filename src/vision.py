import cv2
import pytesseract

def detect_buttons(image_path="screen.png"):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    boxes = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
    
    results = []
    for i, text in enumerate(boxes['text']):
        if text.strip():
            x, y, w, h = boxes['left'][i], boxes['top'][i], boxes['width'][i], boxes['height'][i]
            results.append({"label": text, "x": x, "y": y, "w": w, "h": h})
    return results