import cv2
import numpy as np
from flask import Response
import time

class VideoCamera:
    def __init__(self):
        self.video = cv2.VideoCapture(0)
        self.video.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.detector = cv2.QRCodeDetector()
        self.last_qr_code = None
        self.qr_detected_time = None
        
    def __del__(self):
        self.video.release()
    
    def get_frame(self):
        """Get frame from camera with QR detection overlay"""
        success, frame = self.video.read()
        if not success:
            return None
            
        # Detect QR code
        data, bbox, _ = self.detector.detectAndDecode(frame)
        
        # Draw bounding box if QR code detected
        if bbox is not None:
            bbox = bbox.astype(int)
            for i in range(len(bbox[0])):
                pt1 = tuple(bbox[0][i])
                pt2 = tuple(bbox[0][(i + 1) % len(bbox[0])])
                cv2.line(frame, pt1, pt2, (0, 255, 0), 3)
            
            if data:
                self.last_qr_code = data.strip()
                self.qr_detected_time = time.time()
                cv2.putText(frame, f"QR: {data}", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        else:
            cv2.putText(frame, "Position QR code in view", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        ret, jpeg = cv2.imencode('.jpg', frame)
        return jpeg.tobytes()
    
    def get_last_qr_code(self):
        """Get the last detected QR code"""
        return self.last_qr_code

def generate_frames(camera):
    """Generate frames for video streaming"""
    while True:
        frame = camera.get_frame()
        if frame is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
