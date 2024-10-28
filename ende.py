import os
import re
import time
import shutil
import struct
import serial
import serial.tools.list_ports
from PIL import Image
import io
import hashlib

# Configuration
CHECK_INTERVAL = 0.5
EXTENSIONS = {"jpg", "jpeg", "CR2"}
BASE_DIR = "images"
LAST_RANGE_FILE = "last_range.txt"
RAW_IMAGE_DIR = "images"
PACKET_SIZE = 1024

# Initialize Serial Connection
def find_esp32_port():
    """Finds the serial port to which ESP32 is connected."""
    ports = serial.tools.list_ports.comports()
    for port in ports:
        try:
            ser = serial.Serial(port.device)
            ser.write(b'hello')
            response = ser.readline().strip()
            if response == b'ESP32':  # Assuming ESP32 responds with 'ESP32'
                print(f"ESP32 found on {port.device}")
                return port.device
            ser.close()
        except Exception:
            pass
    return None

def load_image_as_bytes(image_path):
    """Load an image and convert it to bytes."""
    with Image.open(image_path) as img:
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        return img_bytes.getvalue()

def packetize_data(image_data, packet_size=PACKET_SIZE):
    """Divide image data into packets with checksum and sequence number."""
    packets = []
    for i in range(0, len(image_data), packet_size):
        packet_data = image_data[i:i+packet_size]
        checksum = hashlib.sha256(packet_data).digest()
        packet = struct.pack('>I', i // packet_size) + checksum + packet_data
        packets.append(packet)
    return packets

def transmit_data_to_esp32(image_path):
    """Load image, packetize it, detect ESP32 port, and transmit data."""
    image_data = load_image_as_bytes(image_path)
    packets = packetize_data(image_data)

    esp32_port = find_esp32_port()
    if not esp32_port:
        print("ESP32 not detected. Ensure it's connected and try again.")
        return

    with serial.Serial(esp32_port, 115200, timeout=1) as ser:
        for packet in packets:
            ser.write(packet)
            print(f"Packet sent with size {len(packet)} bytes.")
            time.sleep(0.05)  # Adjust based on transmission speed

    print("Image transmission completed.")

# Run the code
image_path = "latest_image.png"  # Path to your captured image
transmit_data_to_esp32(image_path)
