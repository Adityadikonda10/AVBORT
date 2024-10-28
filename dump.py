import os
import time
from googleapiclient.discovery import build
from google.oauth2 import service_account
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

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
            media = file.read()

            # Upload the file to Google Drive
            uploaded_file = service.files().create(
                body=file_metadata,
                media_body=file_path
            ).execute()
            
            print(f"[SUCCESS] Uploaded: {file_path.startswith('raw_') and file_path.endswith(('.jpg', '.jpeg', '.png', '.CR2'))} (ID: {uploaded_file['id']})")
    except Exception as e:
        print(f"[ERROR] Could not upload {file_path}: {str(e)}")

class UploadHandler(FileSystemEventHandler):
    """Handle file system events and upload new files."""
    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith(('.jpg', '.jpeg', '.png')):  # Only image files
            print(f"[EVENT] New image file created: {event.src_path}")
            upload_photo(event.src_path)

if __name__ == "__main__":
    WATCH_FOLDER = 'images'  # Directory to watch for new images

    # Set up observer to monitor the folder
    observer = Observer()
    observer.schedule(UploadHandler(), path=WATCH_FOLDER, recursive=False)
    observer.start()

    print(f"[MONITOR] Watching folder: {WATCH_FOLDER}")
    try:
        while True:
            time.sleep(1)  # Keep the script running
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
