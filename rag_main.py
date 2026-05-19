from pydoc import doc

from utils.debug_logger import DebugLogger
from utils.text_splitter import TextSplitter
from utils.common import load_vectors
from llm_client import LLMClient, OllamaModel
from vector_store import VectorStore
from retriever import Retriever

class RAG:
    def __init__(self, config, model: str = OllamaModel.LLAMA3.value, k_best:int= 2, debug: bool = False):
        self.store = VectorStore()
        self.splitter = TextSplitter(chunk_size=25, overlap=5)
        self.retriever = None
        self.llm = LLMClient(model=model)
        self.debug = DebugLogger(enabled=debug)
        self.k_best = k_best
        self.config = config
        self.initialize()


    def initialize(self):
        self.debug.log("INIT", "Cargando vectores...")
        docs = load_vectors(self.config.get('data').get('database_name'))

        #self.debug.log("SPLIT", "Dividiendo documentos en fragmentos...")
        #chunked_docs = self.splitter.split_documents(docs)
        #self.debug.log("SPLIT", f"{len(chunked_docs)} fragmentos creados a partir de {len(docs)} documentos")

        self.debug.log("EMBED", "Procesando fragmentos y creando embeddings...")
        for doc_id, (text, embedding) in docs.items():
            self.store.add(doc_id, text, embedding)
            self.debug.log("EMBED", f"Fragmento procesado: {doc_id[:30]}...")

        self.retriever = Retriever(self.store, self.k_best)
        self.debug.log("INIT", "Inicialización del sistema RAG completada.")

    def query(self, question: str) -> str:
        if not question.strip():
            return "Please provide a valid question."

        try:
            self.debug.log("QUERY", f"Processing question: {question}")
            context_docs = self.retriever.retrieve(question)
            self.debug.log("RETRIEVE", f"Found {len(context_docs)} relevant documents")
            self.debug.log("RETRIEVE", "Context documents:", context_docs)
            context_text = "\n---\n".join([doc for _, doc in context_docs])

            prompt = f"""
                You are a movie expert assistant. Answer the user's question based on the retrieved movie database context.

                Respond using only the context retrieved from the movie database.
                Do not use any external knowledge or assumptions.
                Avoid making up information and do not give questions back to the user.
                If the answer is not explicitly found in the context, respond with:
                "I cannot answer based on the available database."

                ### Retrieved Context:
                {context_text}

                ### User Question:
                {question}

            ### Answer:
            """

            self.debug.log("LLM", f"Sending prompt to LLM... \n{prompt}...")
            print("\n🎬 Películas encontradas:")
            for score, doc in context_docs:
                first_line = doc.split("\n")[0]
                print(f"- {first_line} | Score: {score:.3f}")

            return self.llm.ask(prompt)
        except Exception as e:
            return f"Error processing query: {str(e)}"


def run_agent(config, model_choice: OllamaModel = None, k_best: int=2, debug: bool = False):
    print("🚀 Iniciando sistema RAG...")
    if model_choice:
        rag = RAG(config=config, model=model_choice.value, k_best=k_best, debug=debug)
    else:
        rag = RAG(config=config)

    print("✅ Sistema RAG listo!")

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


#if __name__ == "__main__":
#    run_agent(OllamaModel.CODE_GEMMA,  3, True)
