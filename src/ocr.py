from winocr import recognize_cv2_sync  # type: ignore

def recognize_text(image):
    result = recognize_cv2_sync(image)
    return result["text"].strip()