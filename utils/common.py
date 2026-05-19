import sqlite3
import numpy as np

def deserialize_embedding(blob_data):
    return np.frombuffer(blob_data, dtype=np.float32)

def load_vectors(db_path="data/movies.db"):
    docs = {}
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        cur.execute("""
            SELECT m.id, m.name, m.description, me.embedding
            FROM movies m
            JOIN movies_embeddings me ON m.id = me.movie_id
        """)
        rows = cur.fetchall()

        for movie_id, name, description, embedding in rows:
            text = f"""Movie: {name}\nDescription: {description or ""}"""
            docs[str(movie_id)] = (text.strip(), (deserialize_embedding(embedding)))

        conn.close()
        print(f"Vectores cargados desde movies.db: {len(docs)}")
        return docs

    except Exception as e:
        print(f"Error loading movies.db: {e}")
        return {}