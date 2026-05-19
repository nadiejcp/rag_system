# from utils.download import download_dataset
from config.load_config import load_config
from utils.web_scrapping import scrape_all_movies_parallel
from vector_store import build_embeddings
from rag_main import run_agent
from llm_client import OllamaModel
import metricas

def main():
  print('Downloading files...')
  config = load_config()

  menu = """
  1. Construir base de datos raw (web scrapping)
  2. Construir base de datos vectorial (generar embeddings)
  3. Ejecutar sistema RAG (responder preguntas)
  4. Revisión de métricas (evaluar desempeño)
  0. Salir
  """
  print("Bienvenido al sistema RAG de películas. Por favor, selecciona la opción que deseas ejecutar:")
  print(menu)

  action = input('Ejecutar opción número: ')
  while action != '0':
    if action == '1':
      print('Iniciando web scrapping y almacenando datos raw...')
      scrape_all_movies_parallel(config.get('data'), max_workers=6)
    elif action == '2':
      print('Generando embeddings y almacenando en la base de datos vectorial...')
      build_embeddings(config)
    elif action == '3':
      run_agent(config, OllamaModel.LLAMA3, k_best=3, debug=False)
    elif action == '4':
      metricas.main()
    else:
      print('Opción no válida. Por favor, selecciona una opción del menú.')

    print("=" * 50)
    print("Menú de opciones:")
    print(menu)
    action = input('Ejecutar opción número: ')

if __name__ == "__main__":
  main()