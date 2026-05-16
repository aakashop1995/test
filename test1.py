import cv2

# Try all common video devices
for i in [0, 1, 2, 3, 12, 13, 14]:
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret and frame is not None:
            print(f"[OK] Device /dev/video{i} works — shape: {frame.shape}")
            cv2.imwrite(f'/tmp/test_video{i}.jpg', frame)
            print(f"[SAVED] /tmp/test_video{i}.jpg")
        else:
            print(f"[FAIL] Device /dev/video{i} opened but no frame")
        cap.release()
    else:
        print(f"[SKIP] /dev/video{i} could not open")
