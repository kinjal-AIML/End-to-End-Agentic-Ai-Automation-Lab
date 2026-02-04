"""
Data Ingestion Script
Run this manually to build/update the Vector Database

Usage:
    python ingest.py --source data/raw/ --rebuild
"""

import argparse
from pathlib import Path
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.services.vector import VectorStoreService
from app.config import settings


def load_documents(source_dir: str):
    """Load documents from directory"""
    print(f"📂 Loading documents from: {source_dir}")
    
    loader = DirectoryLoader(
        source_dir,
        glob="**/*.txt",
        loader_cls=TextLoader
    )
    
    documents = loader.load()
    print(f"✅ Loaded {len(documents)} documents")
    return documents


def split_documents(documents):
    """Split documents into chunks"""
    print("🔪 Splitting documents into chunks...")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    
    chunks = text_splitter.split_documents(documents)
    print(f"✅ Created {len(chunks)} chunks")
    return chunks


def build_vectorstore(chunks, rebuild=False):
    """Build or update vector store"""
    print("🏗️  Building vector store...")
    
    vector_service = VectorStoreService()
    
    if rebuild:
        print("⚠️  Rebuilding from scratch...")
        vector_service.create_vectorstore(chunks)
    else:
        print("📝 Updating existing vectorstore...")
        vector_service.add_documents(chunks)
    
    print("✅ Vector store ready!")


def main():
    parser = argparse.ArgumentParser(description="Ingest documents into vector store")
    parser.add_argument(
        "--source",
        type=str,
        default="data/raw/",
        help="Source directory for documents"
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Rebuild vectorstore from scratch"
    )
    
    args = parser.parse_args()
    
    # Load documents
    documents = load_documents(args.source)
    
    # Split into chunks
    chunks = split_documents(documents)
    
    # Build vectorstore
    build_vectorstore(chunks, rebuild=args.rebuild)
    
    print("\n🎉 Ingestion complete!")


if __name__ == "__main__":
    main()
