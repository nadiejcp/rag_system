from embedder import SimpleEmbedder

class Retriever:
    def __init__(self, store, embedder: SimpleEmbedder, k=2):
        self.store = store
        self.embedder = embedder
        self.k = k

    def retrieve(self, query: str):
        query_vec = self.embedder.embed(query)
        scored = []

        for doc_id, text, vector in self.store.get_all():
            score = self.embedder.cosine(query_vec, vector)
            scored.append((score, text))

        scored.sort(reverse=True, key=lambda x: x[0])
        return scored[:self.k]
