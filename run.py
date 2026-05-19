# from utils.download import download_dataset
from config.load_config import load_config
from utils.web_scrapping import scrape_all_movies_parallel
from vector_store import build_embeddings
from rag_main import run_agent
from llm_client import OllamaModel

def main():
  print('Downloading files...')
  config = load_config()

  if input('¿Deseas construir la base de datos raw? (s/n): ').lower() == 's':
    print('Iniciando web scrapping y almacenando datos raw...')
    scrape_all_movies_parallel(config.get('data'), max_workers=6)

  if input('¿Deseas construir la base de datos vectorial? (s/n): ').lower() == 's':
    print('Generando embeddings y almacenando en la base de datos vectorial...')
    build_embeddings(config)

  print('Iniciando sistema RAG...')
  run_agent(config, OllamaModel.LLAMA3, k_best=3, debug=False)
  print('Proceso completado.')

if __name__ == "__main__":
  main()