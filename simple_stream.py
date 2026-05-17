from flask import Flask, Response
from picamera2 import Picamera2
import cv2
import time

app = Flask(__name__)

# --- Camera setup ---
picam2 = Picamera2()
config = picam2.create_video_configuration(main={"size": (320, 240)})
picam2.configure(config)
picam2.start()

time.sleep(2)  # warm-up camera

# --- Frame generator ---
def generate_frames():
    while True:
        frame = picam2.capture_array()

        # Convert RGB → BGR (important for OpenCV)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        # Encode frame to JPEG
        success, buffer = cv2.imencode('.jpg', frame)
        if not success:
            continue

        frame = buffer.tobytes()

        # MJPEG stream format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

        time.sleep(0.03)  # prevents CPU overload (important for Pi 1GB)

# --- Routes ---
@app.route('/')
def index():
    return "<h1>Raspberry Pi Camera Stream</h1><img src='/video_feed'>"

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# --- Run server ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)
