import cv2

cap = cv2.VideoCapture(0, cv2.CAP_V4L2)

ret, frame = cap.read()
print("read:", ret)

if ret:
    ok, jpg = cv2.imencode(".jpg", frame)
    print("encode:", ok, len(jpg))
