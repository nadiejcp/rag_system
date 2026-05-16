class TextSplitter:
    def __init__(self, chunk_size=500, overlap=50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def split_text(self, text: str) -> list[str]:
        """Split text into chunks with overlap."""
        words = text.split()
        chunks = []

        if len(words) <= self.chunk_size:
            return [text]

        for i in range(0, len(words), self.chunk_size - self.overlap):
            chunk = ' '.join(words[i:i + self.chunk_size])
            chunks.append(chunk)

        return chunks

    def split_documents(self, documents: dict) -> dict:
        """Split multiple documents into chunks."""
        chunked_docs = {}
        for doc_id, text in documents.items():
            chunks = self.split_text(text)
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_chunk_{i}"
                chunked_docs[chunk_id] = chunk
        return chunked_docs
