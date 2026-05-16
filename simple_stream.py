from flask import Flask, Response
import subprocess
import threading
import time

app = Flask(__name__)

latest_frame = None
lock = threading.Lock()

def capture_loop():
    global latest_frame
    cmd = [
        'ffmpeg',
        '-f', 'v4l2',
        '-video_size', '640x480',  # removed -input_format mjpeg
        '-framerate', '30',
        '-i', '/dev/video0',
        '-f', 'image2pipe',
        '-vcodec', 'mjpeg',
        '-q:v', '5',
        'pipe:1'
    ]
    print("[INFO] Starting ffmpeg...")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)  # capture stderr too

    jpg_start = b'\xff\xd8'
    jpg_end   = b'\xff\xd9'
    buf = b''
    frame_count = 0

    while True:
        chunk = proc.stdout.read(4096)
        if not chunk:
            # print ffmpeg error if pipe dies
            err = proc.stderr.read().decode()
            print("[FFMPEG ERROR]", err)
            break

        buf += chunk
        start = buf.find(jpg_start)
        end   = buf.find(jpg_end)

        if start != -1 and end != -1 and end > start:
            jpg = buf[start:end+2]
            buf = buf[end+2:]
            with lock:
                latest_frame = jpg
            frame_count += 1
            if frame_count % 30 == 0:
                print(f"[INFO] Frames captured: {frame_count}, size: {len(jpg)} bytes")

threading.Thread(target=capture_loop, daemon=True).start()

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

from flask import send_file

@app.route('/testimg')
def testimg():
    return send_file('/home/ubuntu/pothole_detection/test/test.jpg')

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
