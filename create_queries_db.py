# Este script crea una base de datos SQLite llamada queries.db a partir del archivo Excel de queries detalladas.
# Guarda este archivo como create_queries_db.py y ejecútalo una vez para crear la base de datos.
import sqlite3
import pandas as pd
import os

# Ruta del archivo Excel y de la base de datos
excel_path = os.path.join('data', 'movies_detailed_natural_language_queries_shuffled.xlsx')
db_path = os.path.join('data', 'queries.db')

def create_db_from_excel(excel_path, db_path):
    # Leer el archivo Excel
    df = pd.read_excel(excel_path)
    # Normalizar nombres de columnas
    df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
    # Crear la base de datos y la tabla
    with sqlite3.connect(db_path) as conn:
        df.to_sql('queries', conn, if_exists='replace', index=False)
    print(f"Base de datos creada en: {db_path}")
    print(f"Filas insertadas: {len(df)}")

if __name__ == "__main__":
    create_db_from_excel(excel_path, db_path)
