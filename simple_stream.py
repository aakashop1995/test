from flask import Flask, Response
import subprocess
import threading
import time

app = Flask(__name__)

# ── Frame buffer ───────────────────────────────────────────────
latest_frame = None
lock = threading.Lock()

def capture_loop():
    global latest_frame
    cmd = [
        'ffmpeg',
        '-f', 'v4l2',
        '-input_format', 'mjpeg',
        '-video_size', '640x480',
        '-framerate', '30',
        '-i', '/dev/video0',
        '-f', 'image2pipe',
        '-vcodec', 'mjpeg',
        '-q:v', '5',
        'pipe:1'
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                 stderr=subprocess.DEVNULL)
    jpg_start = b'\xff\xd8'
    jpg_end   = b'\xff\xd9'
    buf = b''

    while True:
        chunk = proc.stdout.read(4096)
        if not chunk:
            break
        buf += chunk
        start = buf.find(jpg_start)
        end   = buf.find(jpg_end)
        if start != -1 and end != -1 and end > start:
            jpg = buf[start:end+2]
            buf = buf[end+2:]
            with lock:
                latest_frame = jpg

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
