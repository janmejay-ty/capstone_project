import os
import sys
from pypdf import PdfReader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.http import models
from dotenv import load_dotenv

# Load env variables
load_dotenv()

def load_pdf(file_path):
    print(f"Reading PDF: {file_path}")
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        t = page.extract_text()
        if t:
            text += t + "\n"
    
    metadata = {
        "source": os.path.basename(file_path),
        "path": file_path
    }
    return Document(page_content=text, metadata=metadata)

def main():
    docs_dir = r"c:\Users\User\Desktop\python\capstone_project\knowledge\docs"
    
    if not os.path.exists(docs_dir):
        print(f"[ERROR] Knowledge docs directory does not exist: {docs_dir}")
        return

    # 1. Load all PDFs
    documents = []
    for f in os.listdir(docs_dir):
        if f.endswith(".pdf"):
            file_path = os.path.join(docs_dir, f)
            try:
                doc = load_pdf(file_path)
                documents.append(doc)
            except Exception as e:
                print(f"[ERROR] Failed to load {f}: {e}")

    if not documents:
        print("[WARNING] No PDF documents found to ingest.")
        return

    print(f"Loaded {len(documents)} documents. Splitting into chunks...")

    # 2. Split documents
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = text_splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks from documents.")

    # 3. Initialize Qdrant Client (Server/Cloud mode only)
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    collection_name = "resolvedesk_docs"

    if not qdrant_url:
        raise ValueError("QDRANT_URL environment variable is missing. A running Qdrant server/cloud instance is required.")

    print(f"Connecting to Qdrant server/cloud at {qdrant_url}...")
    client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)

    # Recreate collection
    print(f"Recreating Qdrant collection: '{collection_name}'...")
    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE),
    )

    # 4. Generate Embeddings and Upsert
    print("Initializing HuggingFaceEmbeddings (all-MiniLM-L6-v2)...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    print("Embedding chunks and preparing points for upload...")
    points = []
    for i, chunk in enumerate(chunks):
        vector = embeddings.embed_query(chunk.page_content)
        points.append(
            models.PointStruct(
                id=i,
                vector=vector,
                payload={
                    "page_content": chunk.page_content,
                    "source": chunk.metadata["source"],
                    "path": chunk.metadata["path"]
                }
            )
        )

    print(f"Upserting {len(points)} points into Qdrant collection...")
    client.upsert(collection_name=collection_name, points=points)
    print("Ingestion pipeline completed successfully!")

if __name__ == "__main__":
    main()
