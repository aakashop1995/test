import cv2
import numpy as np
import asyncio
from aiohttp import web

from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from av import VideoFrame

pcs = set()

# -----------------------------
# Camera Track (SAFE VERSION)
# -----------------------------
class CameraTrack(VideoStreamTrack):
    def __init__(self):
        super().__init__()
        self.cap = cv2.VideoCapture(0, cv2.CAP_V4L2)

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

    async def recv(self):
        pts, time_base = await self.next_timestamp()

        ret, frame = self.cap.read()

        # IMPORTANT: SAFE FALLBACK
        if not ret or frame is None:
            frame = np.zeros((240, 320, 3), dtype=np.uint8)
        else:
            frame = cv2.resize(frame, (320, 240))

        video_frame = VideoFrame.from_ndarray(frame, format="bgr24")
        video_frame.pts = pts
        video_frame.time_base = time_base

        return video_frame


# -----------------------------
# Offer handler (SAFE)
# -----------------------------
async def offer(request):
    params = await request.json()

    offer = RTCSessionDescription(
        sdp=params["offer"]["sdp"],
        type=params["offer"]["type"]
    )

    pc = RTCPeerConnection()
    pcs.add(pc)

    pc.addTrack(CameraTrack())

    await pc.setRemoteDescription(offer)

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.json_response({
        "answer": {
            "sdp": pc.localDescription.sdp,
            "type": pc.localDescription.type
        }
    })


# -----------------------------
# HTML
# -----------------------------
async def index(request):
    return web.Response(text="""
<!DOCTYPE html>
<html>
<body>
<h2>Pi WebRTC Camera</h2>

<video id="video" autoplay playsinline></video>

<script>
let pc = new RTCPeerConnection();

pc.ontrack = (event) => {
    document.getElementById("video").srcObject = event.streams[0];
};

async function start() {
    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);

    const response = await fetch("/offer", {
        method: "POST",
        body: JSON.stringify({ offer: pc.localDescription }),
        headers: { "Content-Type": "application/json" }
    });

    const data = await response.json();
    await pc.setRemoteDescription(data.answer);
}

start();
</script>

</body>
</html>
""", content_type="text/html")


# -----------------------------
# App
# -----------------------------
app = web.Application()
app.router.add_get("/", index)
app.router.add_post("/offer", offer)

web.run_app(app, host="0.0.0.0", port=8080)
