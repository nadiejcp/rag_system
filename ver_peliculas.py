from vector_store import connect_db, fetch_movies
import csv

if __name__ == "__main__":
    # --- Películas ---
    db_path = "data/movies.db"
    table_name = "movies"
    export_path = r"D:\0. Ciencia de Datos\4. Inteligencia Artificial\4. Semana 4\Proyecto Final\movies_export.csv"

    with connect_db(db_path) as conn:
        movies = fetch_movies(conn, table_name)
        print(f"Total de películas: {len(movies)}\n")
        for movie in movies:
            print(f"ID: {movie['id']}")
            print(f"Nombre: {movie['name']}")
            print(f"Descripción: {movie['description']}")
            print("-" * 40)

        # Exportar a CSV
        with open(export_path, mode="w", encoding="utf-8", newline="") as csvfile:
            fieldnames = ["id", "name", "description"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for movie in movies:
                writer.writerow({
                    "id": movie["id"],
                    "name": movie["name"],
                    "description": movie["description"]
                })
        print(f"\nArchivo CSV exportado a: {export_path}")

    # --- Queries ---
    import sqlite3
    queries_db_path = "data/queries.db"
    print("\nConsultas de ejemplo desde queries.db:\n")
    with sqlite3.connect(queries_db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM queries LIMIT 10")
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        for row in rows:
            print("--- Query ---")
            for col, val in zip(columns, row):
                print(f"{col}: {val}")
            print("-" * 40)
