import cv2

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Skip warmup frames
for i in range(30):
    cap.read()

ret, frame = cap.read()
print("ret:", ret)
print("shape:", frame.shape if frame is not None else "None")
print("mean color (BGR):", frame.mean(axis=(0,1)) if frame is not None else "None")

cv2.imwrite('/tmp/test_opencv.jpg', frame)
print("Saved to /tmp/test_opencv.jpg")
cap.release()
