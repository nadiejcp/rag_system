from embedder import Embedder, cosine

class Retriever:
    def __init__(self, store, k=2):
        self.embedder = Embedder()
        self.store = store
        self.k = k

    def retrieve(self, query: str):
        query_vec = self.embedder.embed_text(query)
        scored = []

        for _, text, vector in self.store.get_all():
            score = cosine(query_vec, vector)
            scored.append((score, text))

        scored.sort(reverse=True, key=lambda x: x[0])
        return scored[:self.k]
