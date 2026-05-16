from utils.download import download_dataset
from config.load_config import load_config
from utils.web_scrapping import scrape_all_movies_parallel

def main():
  print('Downloading files...')
  config = load_config("config/config.yaml")
  download_dataset(config.get('data'))
  scrape_all_movies_parallel(config.get('data'), max_workers=6)
  print('Fin del programa')

if __name__ == "__main__":
  main()