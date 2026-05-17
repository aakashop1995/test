from picamera2 import Picamera2
import time

picam2 = Picamera2()

picam2.configure(picam2.create_preview_configuration(main={"size": (320, 240)}))

picam2.start()

time.sleep(2)

print("Camera started successfully")

frame = picam2.capture_array()

print("Frame shape:", frame.shape)

picam2.stop()
