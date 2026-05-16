import os
import kagglehub
import shutil

def download_dataset():
  BASE_DIR = os.path.dirname(os.path.abspath(__file__))
  DATA_DIR = os.path.join(BASE_DIR, "data")
  os.makedirs(DATA_DIR, exist_ok=True)
  download_path = kagglehub.dataset_download("fayaznoor10/movie-transcripts-59k")
  final_path = os.path.join(DATA_DIR, "movie-transcripts-59k")
  if os.path.exists(final_path):
    shutil.rmtree(final_path)
  shutil.move(download_path, final_path)
  print("Saved dataset at:", final_path)