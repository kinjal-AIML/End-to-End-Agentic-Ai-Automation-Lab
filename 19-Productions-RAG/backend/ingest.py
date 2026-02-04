import os
import json
import pandas as pd
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_community.retrievers import BM25Retriever
import pickle

# Load Keys
load_dotenv()

# Paths
DATA_DIR = "data" # Make sure your json/csv files are in backend/data/
INDEX_PATH = "faiss_index_store"
BM25_PATH = "bm25_retriever.pkl"

def load_and_process_data():
    documents = []
    print("🚀 Starting Data Ingestion...")

    # --- 1. Load Product Catalog (HQI Strategy) ---
    path = os.path.join(DATA_DIR, "product_catalog.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            data = json.load(f)
        for item in data:
            for q in item['indexing_questions']:
                doc = Document(
                    page_content=q,  # Embed the QUESTION
                    metadata={
                        "source": "product_catalog",
                        "answer_content": item['content'], # Retrieve the ANSWER
                        "url_context": item.get('url_context'),
                        "type": "technical"
                    }
                )
                documents.append(doc)
        print(f"✅ Loaded {len(data)} Products.")

    # --- 2. Load FAQ & Business Logic (CSV) ---
    for filename in ["faq.csv", "business_logic.csv"]:
        path = os.path.join(DATA_DIR, filename)
        if os.path.exists(path):
            df = pd.read_csv(path)
            for _, row in df.iterrows():
                doc = Document(
                    page_content=row['question'],
                    metadata={
                        "source": filename.replace(".csv", ""),
                        "answer_content": row['answer'],
                        "type": "faq"
                    }
                )
                documents.append(doc)
            print(f"✅ Loaded {len(df)} rows from {filename}.")

    # --- 3. Load Policy (Chunking) - THIS FIXED YOUR ISSUE ---
    path = os.path.join(DATA_DIR, "policy.txt")
    if os.path.exists(path):
        with open(path, "r") as f:
            policy_text = f.read()
        
        # Split text into chunks
        splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)
        chunks = splitter.create_documents([policy_text])
        
        for chunk in chunks:
            chunk.metadata = {
                "source": "policy",
                "answer_content": chunk.page_content, # For policy, answer is the text itself
                "type": "legal"
            }
            documents.append(chunk)
        print(f"✅ Loaded Policy chunks: {len(chunks)}")

    return documents

def build_indices():
    docs = load_and_process_data()
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    # 1. Build FAISS (Semantic Index)
    print("🧠 Building FAISS Index...")
    vector_store = FAISS.from_documents(docs, embeddings)
    vector_store.save_local(INDEX_PATH)
    
    # 2. Build BM25 (Keyword Index)
    print("📚 Building BM25 Index...")
    bm25_retriever = BM25Retriever.from_documents(docs)
    bm25_retriever.k = 5
    
    # Save BM25 object using Pickle (FAISS saves itself, but BM25 needs pickle)
    with open(BM25_PATH, "wb") as f:
        pickle.dump(bm25_retriever, f)

    print(f"🎉 Ingestion Complete. Index saved to '{INDEX_PATH}' and '{BM25_PATH}'")

if __name__ == "__main__":
    build_indices()