from flask import Flask, Response
import cv2
import time
import threading

app = Flask(__name__)

# -----------------------------
# Camera setup (IMPORTANT)
# -----------------------------
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

# -----------------------------
# Latest frame storage (NO LAG)
# -----------------------------
latest_frame = None
lock = threading.Lock()

def capture_loop():
    global latest_frame

    while True:
        ret, frame = cap.read()

        if not ret or frame is None:
            continue

        # resize for speed
        frame = cv2.resize(frame, (320, 240))

        with lock:
            latest_frame = frame

        time.sleep(0.01)  # small delay to prevent CPU spike

# start capture thread
threading.Thread(target=capture_loop, daemon=True).start()

# -----------------------------
# MJPEG generator (stable)
# -----------------------------
def generate():
    global latest_frame

    while True:
        with lock:
            frame = None if latest_frame is None else latest_frame.copy()

        if frame is None:
            continue

        success, buffer = cv2.imencode('.jpg', frame, [
            int(cv2.IMWRITE_JPEG_QUALITY), 80
        ])

        if not success:
            continue

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' +
               buffer.tobytes() +
               b'\r\n')

        time.sleep(0.03)  # controls FPS (~30 FPS max)

# -----------------------------
# Flask routes
# -----------------------------
@app.route('/')
def home():
    return """
    <html>
        <body>
            <h2>Raspberry Pi Camera Stream</h2>
            <img src="/video" width="640"/>
        </body>
    </html>
    """

@app.route('/video')
def video():
    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# -----------------------------
# Run server
# -----------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
