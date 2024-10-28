import os
import time
import re
import shutil

CHECK_INTERVAL = 0.5  
EXTENSIONS = {"jpg", "jpeg", "CR2"}
BASE_DIR = "images/DCIM"
LAST_RANGE_FILE = "last_range.txt"
BLUE_LED = "blue_led"  
RED_LED = "red_led"
RAW_IMAGE_DIR = "images"  

def blink_led(color):
    print(f"Blinking {color} LED") 

def camera_connected():
    dslr_camera_brands = ["Canon", "Nikon", "Sony", "Pentax", "Olympus", "Leica", "Fujifilm"]
    result = os.popen("gphoto2 --auto-detect").read()
    for model in dslr_camera_brands:
        if model in result:
            blink_led(BLUE_LED)
            return True
        else:
            blink_led(RED_LED)
            return False

def list_files():
    return os.popen("gphoto2 --list-files").read()

def get_last_image_info():
    output = list_files()
    dcim_folder = None
    folders = re.findall(r"\/store.*DCIM\/\d+", output)
    
    if folders:
        max_folder = max(folders, key=lambda f: int(re.findall(r"\d+", f)[-1]))
        dcim_folder = max_folder

    if dcim_folder:
        file_info = re.findall(r"#(\d+)\s+(IMG_\d+\.\w+)", output)
        return dcim_folder, file_info 
    return None, []

def save_range(range_value):
    with open(LAST_RANGE_FILE, "w") as file:
        file.write(str(range_value))

def read_last_range():
    if os.path.exists(LAST_RANGE_FILE):
        with open(LAST_RANGE_FILE, "r") as file:
            content = file.read().strip()
            if content.isdigit():
                return int(content)
    return None

def initialize_last_range():
    dcim_folder, image_info = get_last_image_info()
    if image_info:
        latest_image_serial = int(image_info[-1][0])  # Get the highest serial number
        save_range(latest_image_serial)  # Save it as the initial last range
        print(f"Initialized last range with serial number {latest_image_serial}")
        return latest_image_serial
    return 0  # Default if no files are found

def fetch_images(start, end):
    os.system(f"gphoto2 --get-raw-data {start}-{end}")
    move_images_to_raw_dir()

def move_images_to_raw_dir():
    """Move fetched images from the main directory to the images/raw directory."""
    for filename in os.listdir("/Users/adityadikonda/AVBORT/"):
        for ext in EXTENSIONS:
            if filename.startswith("raw_") and filename.endswith(ext):
                # Define new path in RAW_IMAGE_DIR
                dest_path = os.path.join(RAW_IMAGE_DIR, filename)
                os.makedirs(RAW_IMAGE_DIR, exist_ok=True)
                
                # Move image to RAW_IMAGE_DIR and print message
                shutil.move(filename, dest_path)
                print(f"Saving file as {dest_path}")  # Adjusted print message to reflect new path

def main():
    os.makedirs(BASE_DIR, exist_ok=True)

    if not camera_connected():
        print("Camera not connected")
        # return

    last_range = read_last_range()
    if last_range is None:
        last_range = initialize_last_range()

    while True:
        if camera_connected():
            dcim_folder, image_info = get_last_image_info()
            if image_info:
                # Filter new images that have not been saved
                new_images = [(int(serial), name) for serial, name in image_info if int(serial) > last_range]
                
                if new_images:
                    # Sort by serial number to process images in order
                    new_images.sort()
                    first_new, last_new = new_images[0][0], new_images[-1][0]
                    
                    # If multiple new images, fetch in range; otherwise, fetch the single image
                    if last_new > first_new:
                        fetch_images(first_new, last_new)
                    else:
                        fetch_images(last_new, last_new)

                    # Create DCIM subfolder and rename images to original names
                    dcim_path = os.path.join(BASE_DIR, os.path.basename(dcim_folder))
                    os.makedirs(dcim_path, exist_ok=True)
                    for serial, name in new_images:
                        original_path = os.path.join(RAW_IMAGE_DIR, f"IMG_{serial}.CR2")
                        new_path = os.path.join(dcim_path, name)
                        
                        # Wait briefly for image file completion before renaming
                        time.sleep(1)  # Adjust if needed
                        if os.path.exists(original_path):
                            os.rename(original_path, new_path)
                            print(f"Renamed {original_path} to {new_path}")

                    # Update the last_range.txt with the last new image serial number
                    last_range = last_new
                    save_range(last_range)

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
