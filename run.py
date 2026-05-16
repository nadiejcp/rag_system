from utils.download import download_dataset, download_movies_from_page
from config.load_config import load_config

def main():
  print('Downloading files...')
  config = load_config("config/config.yaml")
  download_dataset(config.get('data'))
  download_movies_from_page(config.get('data'))
  print('Fin del programa')

if __name__ == "__main__":
  main()