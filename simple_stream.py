from flask import Flask, Response
import cv2
import time
import threading

app = Flask(__name__)

# ── Camera init with fallback ──────────────────────────────────
def open_camera():
    # Try plain index first (most reliable on Ubuntu)
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret and frame is not None:
            print("[OK] Camera opened on index 0")
            return cap
        cap.release()

    # Try /dev/video0 explicitly
    cap = cv2.VideoCapture("/dev/video0")
    if cap.isOpened():
        print("[OK] Camera opened via /dev/video0")
        return cap

    print("[ERROR] Could not open camera")
    return None

cap = open_camera()
if cap:
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    # DO NOT set FOURCC — let Ubuntu pick the best format

# ── Frame buffer ───────────────────────────────────────────────
latest_frame = None
lock = threading.Lock()

def capture_loop():
    global latest_frame
    # Warmup: skip first 10 frames
    for _ in range(10):
        cap.read()

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            time.sleep(0.05)
            continue
        frame = cv2.resize(frame, (320, 240))
        with lock:
            latest_frame = frame

threading.Thread(target=capture_loop, daemon=True).start()

# ── MJPEG stream ───────────────────────────────────────────────
def generate():
    while True:
        with lock:
            frame = latest_frame.copy() if latest_frame is not None else None

        if frame is None:
            time.sleep(0.1)
            continue

        success, buffer = cv2.imencode('.jpg', frame,
                                       [cv2.IMWRITE_JPEG_QUALITY, 75])
        if not success:
            continue

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n'
               + buffer.tobytes()
               + b'\r\n')
        time.sleep(0.033)   # ~30 FPS

# ── Routes ─────────────────────────────────────────────────────
@app.route('/')
def home():
    return """
    <html><body style="background:#111;color:#eee;font-family:sans-serif">
        <h2>Camera Stream</h2>
        <img src="/video" width="640" style="border:2px solid #555"/>
    </body></html>
    """

@app.route('/video')
def video():
    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
