import os
import kagglehub

def download_dataset(config):
  BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
  DATA_DIR = os.path.join(BASE_DIR, config.get('path_to_raw'))
  os.makedirs(DATA_DIR, exist_ok=True)
  if os.path.exists(DATA_DIR):
    print("Dataset already exists at:", DATA_DIR)
    return
  kagglehub.dataset_download(config.get('path_to_download'), DATA_DIR)
