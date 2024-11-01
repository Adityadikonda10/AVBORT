import os
import time
import spidev  # SPI library for Raspberry Pi
from lib_nrf24 import NRF24  # NRF24L01 library
import RPi.GPIO as GPIO
from googleapiclient.discovery import build
from google.oauth2 import service_account

# GPIO and SPI setup for NRF24L01
GPIO.setmode(GPIO.BCM)
pipes = [[0xe7, 0xe7, 0xe7, 0xe7, 0xe7], [0xc2, 0xc2, 0xc2, 0xc2, 0xc2]]
nrf = NRF24(GPIO, spidev.SpiDev())
nrf.begin(0, 17)  # CE0, GPIO 17 for CSN
nrf.setPayloadSize(32)
nrf.setChannel(0x76)
nrf.setDataRate(NRF24.BR_1MBPS)
nrf.setPALevel(NRF24.PA_MIN)

nrf.openReadingPipe(1, pipes[1])
nrf.startListening()

# Google Drive API configuration
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'service_account.json'
PARENT_FOLDER_ID = '1jS2ZKF_eA78difWcCjyFpAfVet_ozHEr'

def authenticate():
    """Authenticate and return the Google Drive service."""
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)

def upload_photo(file_path):
    """Upload a photo to Google Drive."""
    service = authenticate()

    file_metadata = {
        'name': os.path.basename(file_path),
        'parents': [PARENT_FOLDER_ID]
    }

    try:
        with open(file_path, 'rb') as file:
            # Upload the file to Google Drive
            uploaded_file = service.files().create(
                body=file_metadata,
                media_body=file_path
            ).execute()
            
            print(f"[SUCCESS] Uploaded: {file_path} (ID: {uploaded_file['id']})")
    except Exception as e:
        print(f"[ERROR] Could not upload {file_path}: {str(e)}")

def receive_and_save_image():
    """Receive data from the ESP32 via NRF24 and save it as an image."""
    while True:
        if nrf.available():
            received_data = []
            nrf.read(received_data, nrf.getDynamicPayloadSize())
            print(f"[RECEIVED] Data: {received_data}")

            # Convert received bytes to image
            img_data = bytearray(received_data)
            file_name = f"images/received_image_{int(time.time())}.jpg"
            os.makedirs("images", exist_ok=True)  # Ensure the directory exists
            with open(file_name, 'wb') as img_file:
                img_file.write(img_data)
                print(f"[SAVED] Image saved to: {file_name}")

            # Upload the saved image to Google Drive
            upload_photo(file_name)

if __name__ == "__main__":
    print("[START] Receiving and uploading images from NRF24L01...")
    try:
        # Start listening for data from ESP32 and save images
        receive_and_save_image()
    except KeyboardInterrupt:
        GPIO.cleanup()
        print("\n[EXIT] Program stopped.")
