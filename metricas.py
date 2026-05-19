"""
metricas.py

Archivo para ejecutar casos de prueba y calcular métricas RAG:
- Accuracy@1
- Recall@3
- MRR
- Faithfulness
- Answer Relevancy
- RAG Global Score

Conexión directa al sistema RAG existente (rag_main.py, llm_client.py, etc).
"""
import sqlite3
from rag_main import RAG

# --- Configuración ---
QUERIES_DB = "data/queries.db"
QUERIES_TABLE = "queries"
EXPECTED_COL = "expected_movie"  # Cambia si el nombre de la columna es diferente
QUERY_COL = "natural_language_query"  # Cambia si el nombre de la columna es diferente
N_TEST = 20  # Número de casos de prueba a ejecutar
K = 3  # Top-K para Recall@3

# --- Cargar casos de prueba desde la base de datos ---
def load_test_cases(db_path=QUERIES_DB, table=QUERIES_TABLE, n=N_TEST):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT {QUERY_COL}, {EXPECTED_COL} FROM {table} WHERE {EXPECTED_COL} IS NOT NULL LIMIT ?", (n,))
    rows = cursor.fetchall()
    conn.close()
    test_cases = [
        {"query": row[0], "expected_movie": row[1]} for row in rows
    ]
    return test_cases

# --- Métricas de retrieval ---
def accuracy_at_1(results):
    correct = 0
    for r in results:
        expected = r["expected_movie"].lower()
        retrieved = r["retrieved_movies"]
        if len(retrieved) > 0 and retrieved[0].lower() == expected:
            correct += 1
    return correct / len(results)

def recall_at_k(results, k=3):
    correct = 0
    for r in results:
        expected = r["expected_movie"].lower()
        retrieved = [movie.lower() for movie in r["retrieved_movies"][:k]]
        if expected in retrieved:
            correct += 1
    return correct / len(results)

def mean_reciprocal_rank(results):
    total_score = 0
    for r in results:
        expected = r["expected_movie"].lower()
        retrieved = [movie.lower() for movie in r["retrieved_movies"]]
        if expected in retrieved:
            rank = retrieved.index(expected) + 1
            total_score += 1 / rank
        else:
            total_score += 0
    return total_score / len(results)

# --- Métricas de generación (manual o con LLM) ---
def faithfulness_manual_score(answer, context):
    print("CONTEXTO:\n", context)
    print("\nRESPUESTA DEL LLM:\n", answer)
    score = float(input("Ingrese score de fidelidad entre 0 y 1: "))
    return score

def answer_relevancy_manual_score(question, answer):
    print("PREGUNTA:\n", question)
    print("\nRESPUESTA:\n", answer)
    score = float(input("Ingrese relevancia entre 0 y 1: "))
    return score

# --- Score global ---
def rag_global_score(acc1, recall3, mrr, faithfulness, answer_relevancy):
    score = (
        0.25 * acc1 +
        0.20 * recall3 +
        0.15 * mrr +
        0.20 * faithfulness +
        0.20 * answer_relevancy
    )
    return score

# --- Ejecución de pruebas ---
def main():
    print("Cargando casos de prueba...")
    test_cases = load_test_cases()
    rag = RAG(k_best=K)
    results = []
    for case in test_cases:
        query = case["query"]
        expected = case["expected_movie"]
        print(f"\nQuery: {query}\nEsperado: {expected}")
        # --- Recuperación ---
        context_docs = rag.retriever.retrieve(query)
        retrieved_movies = []
        context_texts = []
        for score, doc in context_docs:
            # Extraer nombre de la película del chunk recuperado
            first_line = doc.split(".\n")[0].replace("Movie: ", "").strip()
            retrieved_movies.append(first_line)
            context_texts.append(doc)
        # --- Generación ---
        context_text = "\n---\n".join(context_texts)
        answer = rag.llm.ask(rag.query(query))
        results.append({
            "query": query,
            "expected_movie": expected,
            "retrieved_movies": retrieved_movies,
            "retrieved_context": context_text,
            "generated_answer": answer
        })
    # --- Métricas de retrieval ---
    acc1 = accuracy_at_1(results)
    recall3 = recall_at_k(results, k=K)
    mrr = mean_reciprocal_rank(results)
    print(f"\nAccuracy@1: {acc1:.2f}")
    print(f"Recall@3: {recall3:.2f}")
    print(f"MRR: {mrr:.2f}")
    # --- Métricas de generación (manual) ---
    faithfulness_scores = []
    relevancy_scores = []
    for r in results:
        print("\n--- Evaluación manual de generación ---")
        f_score = faithfulness_manual_score(r["generated_answer"], r["retrieved_context"])
        a_score = answer_relevancy_manual_score(r["query"], r["generated_answer"])
        faithfulness_scores.append(f_score)
        relevancy_scores.append(a_score)
    faithfulness = sum(faithfulness_scores) / len(faithfulness_scores)
    answer_relevancy = sum(relevancy_scores) / len(relevancy_scores)
    print(f"Faithfulness: {faithfulness:.2f}")
    print(f"Answer Relevancy: {answer_relevancy:.2f}")
    # --- Score global ---
    score = rag_global_score(acc1, recall3, mrr, faithfulness, answer_relevancy)
    print(f"\nRAG Global Score: {score:.2f}")
    if score >= 0.9:
        print("Sistema Excelente")
    elif score >= 0.8:
        print("Sistema Muy Bueno")
    elif score >= 0.7:
        print("Sistema Bueno")
    else:
        print("Sistema necesita mejoras")

if __name__ == "__main__":
    main()
