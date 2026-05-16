from utils.debug_logger import DebugLogger
from utils.text_splitter import TextSplitter
from utils.common import load_documents
from llm_client import LLMClient, OllamaModel
from embedder import SimpleEmbedder
from vector_store import VectorStore
from retriever import Retriever

class RAG:
    def __init__(self, model: str = OllamaModel.CODE_GEMMA.value, k_best:int= 2, debug: bool = False):
        self.embedder = SimpleEmbedder()
        self.store = VectorStore()
        self.splitter = TextSplitter(chunk_size=25, overlap=5)
        self.retriever = None
        self.llm = LLMClient(model=model)
        self.debug = DebugLogger(enabled=debug)
        self.k_best = k_best
        self.initialize()


    def initialize(self):
        self.debug.log("INIT", "Loading documents...")
        docs = load_documents()

        self.debug.log("SPLIT", "Splitting documents into chunks...")
        chunked_docs = self.splitter.split_documents(docs)
        print(chunked_docs)
        self.debug.log("SPLIT", f"Created {len(chunked_docs)} chunks")

        self.debug.log("EMBED", "Processing chunks and creating embeddings...")
        for doc_id, text in chunked_docs.items():
            vec = self.embedder.embed(text)
            self.store.add(doc_id, text, vec)
            self.debug.log("EMBED", f"Processed chunk: {doc_id[:30]}...")

        self.retriever = Retriever(self.store, self.embedder, self.k_best)
        self.debug.log("INIT", "RAG system initialization complete")

    def query(self, question: str) -> str:
        if not question.strip():
            return "Please provide a valid question."

        try:
            self.debug.log("QUERY", f"Processing question: {question}")
            context_docs = self.retriever.retrieve(question)
            self.debug.log("RETRIEVE", f"Found {len(context_docs)} relevant documents")
            self.debug.log("RETRIEVE", "Context documents:", context_docs)
            context_text = "\n---\n".join([doc for _, doc in context_docs])

            prompt = f"""Responde a la siguiente pregunta basándote únicamente en el contexto proporcionado. Si no 
            encuentras la respuesta en el contexto, indica "No puedo responder basándome en el contexto proporcionado."

                ### Contexto:
                inicio: (
                {context_text}
                ) fin
                
                ### Pregunta:
                {question}

                ### Respuesta:"""

            self.debug.log("LLM", f"Sending prompt to LLM... \n{prompt}...")
            return self.llm.ask(prompt)
        except Exception as e:
            return f"Error processing query: {str(e)}"


def run_agent(model_choice: OllamaModel = None, k_best: int=2, debug: bool = False):
    print("🚀 Initializing RAG system...")
    if model_choice:
        rag = RAG(model=model_choice.value, k_best=k_best, debug=debug)
    else:
        rag = RAG()

    print("✅ RAG system ready!")

    while True:
        try:
            question = input("\n❓ Pregunta (or 'exit' to quit): ").strip()
            if question.lower() == 'exit':
                break
            if not question:
                continue

            print("\n🔄 Processing...")
            answer = rag.query(question)
            print("\n🤖 Respuesta:")
            print(answer)

        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    run_agent(OllamaModel.CODE_GEMMA,  1, True)
