import cv2
import asyncio
from aiohttp import web
from aiortc import RTCPeerConnection, VideoStreamTrack
from av import VideoFrame

pcs = set()

# -----------------------------
# Camera Track
# -----------------------------
class CameraStream(VideoStreamTrack):
    def __init__(self):
        super().__init__()
        self.cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

    async def recv(self):
        pts, time_base = await self.next_timestamp()

        ret, frame = self.cap.read()
        if not ret:
            return None

        frame = cv2.resize(frame, (320, 240))

        video_frame = VideoFrame.from_ndarray(frame, format="bgr24")
        video_frame.pts = pts
        video_frame.time_base = time_base

        return video_frame


# -----------------------------
# WebRTC Offer handler
# -----------------------------
async def offer(request):
    params = await request.json()

    pc = RTCPeerConnection()
    pcs.add(pc)

    pc.addTrack(CameraStream())

    await pc.setRemoteDescription(params["offer"])
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.json_response({"answer": pc.localDescription})


# -----------------------------
# Simple HTML page
# -----------------------------
async def index(request):
    return web.Response(text="""
<!DOCTYPE html>
<html>
<body>
<h2>Pi Camera WebRTC</h2>
<video id="video" autoplay playsinline></video>

<script>
let pc = new RTCPeerConnection();

pc.ontrack = (event) => {
    document.getElementById("video").srcObject = event.streams[0];
};

async function start() {
    let offer = await pc.createOffer();
    await pc.setLocalDescription(offer);

    let response = await fetch("/offer", {
        method: "POST",
        body: JSON.stringify({offer: pc.localDescription}),
        headers: {"Content-Type": "application/json"}
    });

    let data = await response.json();
    await pc.setRemoteDescription(data.answer);
}

start();
</script>
</body>
</html>
""", content_type="text/html")


# -----------------------------
# App setup
# -----------------------------
app = web.Application()
app.router.add_get("/", index)
app.router.add_post("/offer", offer)

# -----------------------------
# Run server
# -----------------------------
web.run_app(app, host="0.0.0.0", port=8080)
