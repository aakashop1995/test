from flask import Flask, Response
import cv2
import time

app = Flask(__name__)

cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

def generate():
    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            continue

        frame = cv2.resize(frame, (320, 240))

        success, buffer = cv2.imencode('.jpg', frame)
        if not success:
            continue

        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' +
               frame_bytes +
               b'\r\n')

        time.sleep(0.03)

@app.route('/')
def home():
    return """
    <html>
    <body>
    <h2>Camera Stream</h2>
    <img src="/video" />
    </body>
    </html>
    """

@app.route('/video')
def video():
    return Response(
        generate(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
