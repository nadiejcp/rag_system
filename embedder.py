import math
import re

class SimpleEmbedder:
    def __init__(self, dim: int = 128):
        self.dim = dim

    def _hash_word(self, w: str):
        h = hash(w)
        vec = [0.0] * self.dim
        vec[h % self.dim] = 1.0
        return vec

    def embed(self, text: str):
        words = re.findall(r"\w+", text.lower())
        if not words:
            return [0.0] * self.dim

        vectors = [self._hash_word(w) for w in words]
        avg = [sum(col) / len(vectors) for col in zip(*vectors)]
        return avg

    @staticmethod
    def cosine(v1, v2):
        dot = sum(a * b for a, b in zip(v1, v2))
        n1 = math.sqrt(sum(a * a for a in v1))
        n2 = math.sqrt(sum(b * b for b in v2))
        return dot / (n1 * n2) if n1 and n2 else 0.0
