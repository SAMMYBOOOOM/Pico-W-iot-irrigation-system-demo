# Smart IoT Irrigation System with Raspberry Pi Pico W

This project is an IoT-based irrigation system built using the Raspberry Pi Pico W microcontroller. The system integrates various sensors, actuators, and communication modules to monitor and control the irrigation process. It features a local web interface, real-time data visualization, and remote control via MQTT and LINE messaging API.

## Table of Contents
- [Introduction](#Introduction)
- [Components](#Components)
- [Functionality](#Functionality)
- [Getting Started](#Getting Started)
- [License](#license)

![pic0](https://github.com/SAMMYBOOOOM/Pico-W-iot-irrigation-system-demo/blob/main/img/pic0.png)
![pic1](https://github.com/SAMMYBOOOOM/Pico-W-iot-irrigation-system-demo/blob/main/img/pic1.png)
![terminal](https://github.com/SAMMYBOOOOM/Pico-W-iot-irrigation-system-demo/blob/main/img/terminal.png)
![line](https://github.com/SAMMYBOOOOM/Pico-W-iot-irrigation-system-demo/blob/main/img/line.png)
![mqtt](https://github.com/SAMMYBOOOOM/Pico-W-iot-irrigation-system-demo/blob/main/img/mqtt.png)

## Introduction:
The Raspberry Pi Pico W Irrigation System is designed to automate the process of watering plants based on soil moisture levels. The system uses a moisture sensor to monitor the soil's moisture content and controls a water pump via a relay. The system also includes an OLED display for local monitoring, a web interface for remote control, and integration with LINE messaging API and MQTT for notifications and remote commands.

## Components:
Used (In demo)
| Component         | Used |
| ----------------- | ---- |
| OLED              | Y    |
| SI1145            | N    |
| External button   | Y    |
| Moisture sensor   | Y    |
| DHT11             | N    |
| Relay             | Y    |
| C270              | Y    |
| Pico W multi core | Y    |
| Water pump(Relay) | Y    |

## Functionality:
| Functionality                    | Implemented |
| -------------------------------- | ----------- |
| OLED display                     | Y           | 
| Wifi                             | Y           |
| Local webUI                      | Y           |
| Local image stream(frame per 5s) | Y           |
| Line messaging api(send)         | Y           |
| Line messaging api(receive)      | Y           |
| Line messaging api(image)        | N           |
| mqtt(send mul)                   | Y           |
| mqtt(receive single)             | Y           |
| Multicore                        | Y           |
When browsing the imageStream site, part of IoT will stop working

## Getting Started
1. Clone the repository:
2. Install dependencies:
Ensure you have the necessary [libraries](https://github.com/SAMMYBOOOOM/Pico-W-iot-irrigation-system-demo/tree/main/lib) installed for the Raspberry Pi Pico W.
Install the required Python packages for the C270 streaming service.
3. Upload the code to your Raspberry Pi Pico W:
Use the Arduino IDE or any compatible tool to upload [demo.ino](https://github.com/SAMMYBOOOOM/Pico-W-iot-irrigation-system-demo/blob/main/code/demo.ino) to your Pico W. Then plug in the modules accordingly.
![wire](https://github.com/SAMMYBOOOOM/Pico-W-iot-irrigation-system-demo/blob/main/img/wire.png)
5. Run the C270 streaming service: 
Run the [capture.py](https://github.com/SAMMYBOOOOM/Pico-W-iot-irrigation-system-demo/blob/main/code/capture.py) to start the streaming service
6. Access the web interface:
http://picow/
7. Expose the local network:
Use tool like [ngrok](https://ngrok.com/) with command:
```cmd
ngrok http http://picow/
```
then put the <ngrok_link>/webhook in Webhook URL for Pico W able to receive message from Line messaging API

### C270 Python Streaming Service (Run this on the local device)
The system includes a Python-based streaming service for the C270 webcam, which captures and streams images to the local web interface. The service is built using Flask and OpenCV.
```python
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
```

## License
This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0). 
