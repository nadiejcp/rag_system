import json
import sqlite3
from pathlib import Path
from typing import List, Sequence

from config.load_config import load_config
from embedder import create_embedder

def connect_db(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

def ensure_embeddings_table(
    conn: sqlite3.Connection,
    table_name: str,
    source_table: str,
) -> None:
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            Table_id INTEGER PRIMARY KEY AUTOINCREMENT,
            Movie_id INTEGER NOT NULL UNIQUE,
            Embedding TEXT NOT NULL,
            FOREIGN KEY(Movie_id) REFERENCES {source_table}(Movie_id)
        )
        """
    )
    conn.commit()

def fetch_movies(conn: sqlite3.Connection, table_name: str) -> List[sqlite3.Row]:
    cursor = conn.execute(
        f"""
        SELECT Movie_id, Movie_name, Description
        FROM {table_name}
        ORDER BY Movie_id ASC
        """
    )
    return cursor.fetchall()

def build_embedding_text(movie_name: str, description: str | None) -> str:
    movie_name = (movie_name or "").strip()
    description = (description or "").strip()
    if movie_name and description:
        return f"Movie: {movie_name}.\n Description: {description}"
    return movie_name or description

def serialize_embedding(embedding: Sequence[float]) -> str:
    return json.dumps([float(x) for x in embedding], ensure_ascii=False)

def upsert_embedding(
    conn: sqlite3.Connection,
    movie_id: int,
    embedding: Sequence[float],
    table_name: str,
) -> None:
    conn.execute(
        f"""
        INSERT INTO {table_name} (Movie_id, Embedding)
        VALUES (?, ?)
        ON CONFLICT(Movie_id) DO UPDATE SET
            Embedding = excluded.Embedding
        """,
        (movie_id, serialize_embedding(embedding)),
    )

def populate_embeddings(
    db_path: str | Path,
    source_table: str,
    target_table: str,
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
) -> int:
    """Read movies from SQLite and store embeddings in a second table.

    Returns the number of processed rows.
    """
    db_path = Path(db_path)
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    embedder = create_embedder(model_name=model_name)

    with connect_db(db_path) as conn:
        ensure_embeddings_table(conn, target_table, source_table)
        movies = fetch_movies(conn, source_table)

        count = 0
        for row in movies:
            movie_id = int(row["Movie_id"])
            text = build_embedding_text(row["Movie_name"], row["Description"])
            if not text:
                continue

            embedding = embedder.embed_text(text)
            upsert_embedding(conn, movie_id, embedding, target_table)
            count += 1

        conn.commit()
        return count


def build_embeddings(config = None) -> None:
    if config is None:
        config = load_config()
        
    data_config = config.get("data", {})
    embedder_config = config.get("embedder", {})

    db_path = data_config.get("database_name")
    if not db_path:
        raise ValueError("Missing 'data.database_name' in config/config.yaml")

    source_table = data_config.get("raw_table_name")
    target_table = data_config.get("embeddings_table_name")
    model_name = embedder_config.get("model_name", "sentence-transformers/all-MiniLM-L6-v2")

    processed = populate_embeddings(
        db_path=db_path,
        source_table=source_table,
        target_table=target_table,
        model_name=model_name,
    )
    print(f"Embeddings stored for {processed} movies in '{target_table}'.")