from typing import List, Sequence

from config.load_config import load_config

class Embedder:
    def __init__(self, config = load_config().get('embedder')):
        self.config = config
        self._model = self._load_model(config.get('model_name'))

    @staticmethod
    def _load_model(model_name: str):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "sentence-transformers is required. Install it with: pip install sentence-transformers"
            ) from exc

        return SentenceTransformer(model_name)

    def embed_text(self, text: str) -> List[float]:
        """Return a single embedding as a plain Python list of floats."""
        if not isinstance(text, str) or not text.strip():
            raise ValueError("text must be a non-empty string")

        vector = self._model.encode(
            text,
            normalize_embeddings=self.config.get('normalize_embeddings'),
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return vector.astype(float).tolist()

    def embed_texts(self, texts: Sequence[str]) -> List[List[float]]:
        """Return embeddings for many texts."""
        cleaned = [t for t in texts if isinstance(t, str) and t.strip()]
        if not cleaned:
            raise ValueError("texts must contain at least one non-empty string")

        vectors = self._model.encode(
            cleaned,
            normalize_embeddings=self.config.get('normalize_embeddings'),
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return [row.astype(float).tolist() for row in vectors]


# Convenience functions -----------------------------------------------------

def create_embedder(model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> Embedder:
    """Factory helper used by other modules."""
    config = load_config().get('embedder')
    config['model_name'] = model_name
    return Embedder(config)

def embed_text(text: str, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> List[float]:
    """One-shot helper for a single text."""
    return create_embedder(model_name).embed_text(text)

def embed_texts(texts: Sequence[str], model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> List[List[float]]:
    """One-shot helper for multiple texts."""
    return create_embedder(model_name).embed_texts(texts)