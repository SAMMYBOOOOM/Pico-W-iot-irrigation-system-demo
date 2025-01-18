# Working
import cv2
import time
from flask import Flask, Response, render_template_string
from threading import Thread, Event
from datetime import datetime
import socket

app = Flask(__name__)

running = True
stop_event = Event()

def add_timestamp(frame):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cv2.putText(frame, timestamp, (frame.shape[1] - 190, frame.shape[0] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    return frame

def gen_frames():
    global running
    cap = cv2.VideoCapture(0)  # Use the primary camera (Logitech C270)
    
    if not cap.isOpened():
        print("Failed to open webcam. Exiting...")
        stop_event.set()
        return

    print(f"Webcam opened successfully. Resolution: {cap.get(cv2.CAP_PROP_FRAME_WIDTH)}x{cap.get(cv2.CAP_PROP_FRAME_HEIGHT)}")
    
    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break
        
        frame = add_timestamp(frame)
        frame = cv2.resize(frame, (320, 240))
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 50]
        ret, buffer = cv2.imencode('.jpg', frame, encode_param)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        
        # Wait for 5 seconds before sending the next frame
        time.sleep(5)
    
    cap.release()
    print("Video capture ended.")

@app.route('/')
def index():
    return render_template_string("<h1>Python Webcam Server</h1><img src='/video_feed'>")

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

def run_app():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def run_video():
    for _ in gen_frames():
        if stop_event.is_set():
            break

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

if __name__ == '__main__':
    local_ip = get_ip()
    print(f"Local IP address: {local_ip}")
    print(f"Flask server will run on http://{local_ip}:5000")
    
    flask_thread = Thread(target=run_app)
    flask_thread.start()
    
    video_thread = Thread(target=run_video)
    video_thread.start()
    
    print("Webcam feed opened. Press 'q' in the video window to quit.")
    
    try:
        while not stop_event.is_set():
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Keyboard interrupt received. Shutting down.")
    finally:
        stop_event.set()
        video_thread.join()
        flask_thread.join(timeout=1)
        print("Application closed.")