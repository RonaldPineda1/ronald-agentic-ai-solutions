import requests
import json
import chromadb
import argparse

# --- 1. Configuration ---
OLLAMA_ENDPOINT = "http://localhost:11434/api"
OLLAMA_CONFIG = {
    "model": "llama3",
    "stream": False,
}
CHROMA_DB_PATH = "./chroma_db"
COLLECTION_NAME = "faq_collection"

# --- 2. Knowledge Base ---
# In a real-world scenario, this would come from a file, database, or API.
FAQ_DATA = [
    {"id": "faq1", "question": "What is the return policy?", "answer": "You can return any item within 30 days of purchase for a full refund."},
    {"id": "faq2", "question": "How do I track my order?", "answer": "Once your order has shipped, you will receive an email with a tracking number."},
    {"id": "faq3", "question": "Do you ship internationally?", "answer": "Yes, we ship to most countries worldwide. Shipping costs may vary."},
    {"id": "faq4", "question": "How can I contact customer support?", "answer": "You can reach our customer support team via email at support@example.com or by calling our toll-free number."},
    {"id": "faq5", "question": "What payment methods do you accept?", "answer": "We accept all major credit cards, PayPal, and Apple Pay."},
    {"id": "faq6", "question": "Can I change my shipping address?", "answer": "If your order has not yet shipped, you can contact customer support to update your shipping address."},
    {"id": "faq7", "question": "What are your business hours?", "answer": "Our customer support is available Monday to Friday, from 9 AM to 5 PM EST."},
    {"id": "faq8", "question": "Do you offer gift wrapping?", "answer": "Yes, we offer gift wrapping for an additional fee. You can select this option at checkout."},
    {"id": "faq9", "question": "How do I use a discount code?", "answer": "You can apply your discount code in the 'Promo Code' box at checkout."},
    {"id": "faq10", "question": "What if my item is damaged?", "answer": "If your item arrives damaged, please contact customer support immediately for a replacement or refund."}
]

# --- 3. ChromaDB Setup ---
client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
collection = client.get_or_create_collection(name=COLLECTION_NAME)

# --- 4. Helper Functions ---
def build_result_items(results):
    items = []
    if not results or not results.get("documents"):
        return items

    docs = results.get("documents", [[]])[0]
    ids = results.get("ids", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    dists = results.get("distances", [[]])[0] if results.get("distances") else [None] * len(docs)

    for i, doc in enumerate(docs):
        items.append({
            "id": ids[i] if i < len(ids) else None,
            "document": doc,
            "metadata": metas[i] if i < len(metas) else {},
            "distance": dists[i] if i < len(dists) else None,
        })
    return items

def format_items_as_bullets(items):
    if not items:
        return "No relevant information found."
    return "\n- " + "\n- ".join(
        f"[{it.get('id')}] {it.get('document')}" for it in items
    )

def search_items(items, term):
    t = term.lower()
    return [
        it for it in items
        if (str(it.get("id", "")).lower().find(t) != -1) or
           (str(it.get("document", "")).lower().find(t) != -1) or
           (json.dumps(it.get("metadata", {})).lower().find(t) != -1)
    ]


def get_embedding(text):
    """
    Generates an embedding for the given text using the Ollama API.
    """
    try:
        response = requests.post(
            f"{OLLAMA_ENDPOINT}/embeddings",
            json={"model": OLLAMA_CONFIG["model"], "prompt": text}
        )
        response.raise_for_status()
        return response.json()["embedding"]
    except requests.exceptions.RequestException as e:
        print(f"Error getting embedding: {e}")
        return None

def index_knowledge_base():
    """
    Indexes the knowledge base into ChromaDB.
    """
    print("Indexing knowledge base...")
    for item in FAQ_DATA:
        # We are embedding the questions to find similar user queries.
        embedding = get_embedding(item["question"])
        if embedding:
            collection.add(
                ids=[item["id"]],
                embeddings=[embedding],
                documents=[item["answer"]],  # Store the answer as the document
                metadatas=[{"question": item["question"]}]
            )
    print("Indexing complete.")

def query_rag_agent(user_query, count, top_k=2, no_context=False):
    """
    Queries the RAG agent with a user's question.
    """
    print(f"\n--- Querying {count} for: '{user_query}' ---")
    
    # 1. Get embedding for the user query
    query_embedding = get_embedding(user_query)
    if not query_embedding:
        return "Sorry, I couldn't process your query."

    # 2. Query ChromaDB for relevant context
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k  # Retrieve the top K most relevant documents
    )
    citations =  results.get('ids')[0] if results.get('ids') else []
    documents = results.get('documents')[0] if results.get('documents') else []

    formatted_context = "\n".join(
        f"\n---CONTEXT BLOCK {i+1}---\n {text}"
        for i, text in enumerate(documents)
    )

    # 3. Construct the prompt for the LLM
    context = (
        f"Here is some context that might be relevant: '{formatted_context}'"
        if not no_context and documents and len(documents) > 0
        else ""
    )
    prompt = f"""
    You are a helpful FAQ assistant. A user has asked the following question:
    '{user_query}'

    {context}

    Based on this context, please provide a clear and concise answer. If the context is not relevant, say so.
    """
    print(f"\nPrompt:\n{prompt}")

    # 4. Send the prompt to the LLM
    try:
        response = requests.post(
            f"{OLLAMA_ENDPOINT}/generate",
            json={"prompt": prompt, **OLLAMA_CONFIG}
        )
        response.raise_for_status()
        return json.loads(response.text)["response"], citations
    except requests.exceptions.RequestException as e:
        return f"Error communicating with the model: {e}"

# --- 5. Main Execution ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--k", type=int, default=2, help="Integer parameter top_k for context retrieval")
    parser.add_argument("--no-context", action="store_true", help="No-context control | Allow generation without retrieval")
    parser.add_argument("--query", help="--query `...`")
    args = parser.parse_args()

    # Check if the collection is empty before indexing
    if collection.count() == 0:
        index_knowledge_base()
    else:
        print("Knowledge base is already indexed.")

    # --- Test Queries ---
    test_queries = [
        "How can I return a product?",
        "What's the process for tracking my package?",
        "Do you ship to Canada?",
        # "What are the support hours?",
        # "Can I pay with Bitcoin?" # A question not in the knowledge base
    ]

    count = 1
    top_k = args.k
    query = args.query
    no_context = args.no_context
    print(f"Params:  top_k={top_k}, query={query}, no_context={no_context}")
    for query in test_queries:
        answer, citations = query_rag_agent(query, count, top_k, no_context)
        print(f"\n\nAnswer: \n\n {answer}, \n\nCitations: {citations}\n\n")
        count += 1
