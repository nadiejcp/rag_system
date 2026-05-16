class VectorStore:
    def __init__(self):
        self.entries = []  # lista de (id, texto, vector)

    def add(self, doc_id: str, text: str, embedding: list):
        self.entries.append((doc_id, text, embedding))

    def get_all(self):
        return self.entries
