import cv2

cap = cv2.VideoCapture(0)
print("Opened:", cap.isOpened())

ret, frame = cap.read()
print("Frame read:", ret)
print("Frame shape:", frame.shape if frame is not None else "None")

cap.release()
