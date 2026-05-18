import sqlite3


<<<<<<< Updated upstream
def load_documents(db_path="data/movies.db"):
=======
def load_documents(db_path="data/raw/movies.db"):
>>>>>>> Stashed changes
    docs = {}

    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        cur.execute("""
            SELECT id, name, description
            FROM movies
            WHERE name IS NOT NULL
        """)

        rows = cur.fetchall()

        for movie_id, name, description in rows:
            text = f"""
Movie: {name}
Description: {description or ""}
"""
            docs[str(movie_id)] = text.strip()

        conn.close()

        print(f"Películas cargadas desde movies.db: {len(docs)}")
        return docs

    except Exception as e:
        print(f"Error loading movies.db: {e}")
        return {}