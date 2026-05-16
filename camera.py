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

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' +
               buffer.tobytes() +
               b'\r\n')

        time.sleep(0.03)  # IMPORTANT for stability

@app.route('/video')
def video():
    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
