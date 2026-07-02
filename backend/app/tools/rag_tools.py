import os
from qdrant_client import QdrantClient
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Initialize Qdrant client and Embeddings once for reuse
qdrant_url = os.getenv("QDRANT_URL")
qdrant_api_key = os.getenv("QDRANT_API_KEY")

if not qdrant_url:
    raise ValueError("QDRANT_URL environment variable is missing. A running Qdrant server/cloud instance is required.")

client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
collection_name = "resolvedesk_docs"

def query_knowledge_base(query: str, limit: int = 3):
    """
    Search the ResolveDesk AI knowledge base PDFs stored in Qdrant.
    Returns a list of raw text chunks that match the query semantically.
    """
    try:
        vector = embeddings.embed_query(query)
        results = client.query_points(
            collection_name=collection_name,
            query=vector,
            limit=limit
        )
        return [point.payload["page_content"] for point in results.points if point.payload and "page_content" in point.payload]
    except Exception as e:
        print(f"[RAG ERROR] Query '{query}' failed: {e}")
        return []
