from flask import Flask, Response
import cv2
import time

app = Flask(__name__)

cap = cv2.VideoCapture(0, cv2.CAP_V4L2)

def generate():
    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.resize(frame, (640, 480))

        _, buffer = cv2.imencode('.jpg', frame)

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' +
               buffer.tobytes() +
               b'\r\n')

        time.sleep(0.03)

@app.route('/video_feed')
def video_feed():
    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

app.run(host='0.0.0.0', port=5000, threaded=True)
