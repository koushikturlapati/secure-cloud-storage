import json
import os 
from datetime import datetime
METADATA_FILE = "metadata.json"
def save_metadata(data):
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r") as file:
            metadata = json.load(file)
    else:
        metadata = []
    metadata.append(data)
    with open(METADATA_FILE, "w") as file:
        json.dump(metadata, file)
def get_metadata():
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r") as file:
            return json.load(file)
    return[]    
        
            
