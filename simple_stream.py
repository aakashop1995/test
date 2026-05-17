from flask import Flask, Response
from picamera2 import Picamera2
import time

app = Flask(__name__)

picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (320, 240)}))
picam2.start()

time.sleep(2)

def generate_frames():
    while True:
        # Get JPEG directly from encoder
        frame = picam2.capture_array()

        import cv2
        success, buffer = cv2.imencode('.jpg', frame)
        if not success:
            continue

        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return "<h1>Camera Stream</h1><img src='/video_feed'>"

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

app.run(host="0.0.0.0", port=5000, threaded=True)
