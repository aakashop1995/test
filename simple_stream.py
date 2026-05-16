import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')

from flask import Flask, Response
from picamera2 import Picamera2
import cv2
import threading
import time

app = Flask(__name__)

# ── Camera setup ───────────────────────────────────────────────
picam2 = Picamera2()
config = picam2.create_video_configuration(
    main={"size": (640, 480), "format": "RGB888"},
    controls={"FrameRate": 30}
)
picam2.configure(config)
picam2.start()
time.sleep(1)  # warmup

# ── Frame buffer ───────────────────────────────────────────────
latest_frame = None
lock = threading.Lock()

def capture_loop():
    global latest_frame
    while True:
        frame = picam2.capture_array()
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        success, buffer = cv2.imencode('.jpg', frame_bgr,
                                       [cv2.IMWRITE_JPEG_QUALITY, 80])
        if success:
            with lock:
                latest_frame = buffer.tobytes()
        time.sleep(0.033)

threading.Thread(target=capture_loop, daemon=True).start()

# ── MJPEG generator ────────────────────────────────────────────
def generate():
    while True:
        with lock:
            frame = latest_frame

        if frame is None:
            time.sleep(0.1)
            continue

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n'
               + frame
               + b'\r\n')
        time.sleep(0.033)

# ── Routes ─────────────────────────────────────────────────────
@app.route('/')
def home():
    return """
    <html><body style="background:#111;color:#eee;font-family:sans-serif;text-align:center">
        <h2>Pi Camera Stream</h2>
        <img src="/video" width="640" style="border:2px solid #444;border-radius:8px"/>
    </body></html>
    """

@app.route('/video')
def video():
    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
