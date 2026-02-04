import os
import pickle
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from app.config import Config
from app.services.llm import embedding_model

class RetrieverService:
    _instance = None
    faiss_retriever = None
    bm25_retriever = None

    def __new__(cls):
        """Singleton Pattern to load the indices only once."""
        if cls._instance is None:
            cls._instance = super(RetrieverService, cls).__new__(cls)
            cls._instance._load_indices()
        return cls._instance

    def _load_indices(self):
        """Loads FAISS and BM25 from disk."""
        print("🔄 Loading Vector Indices...")
        
        try:
            # 1. Load Semantic Index (FAISS)
            if os.path.exists(Config.FAISS_INDEX_PATH):
                vector_store = FAISS.load_local(
                    Config.FAISS_INDEX_PATH, 
                    embedding_model,
                    allow_dangerous_deserialization=True
                )
                # We fetch more candidates (k=10) for RRF to re-rank effectively
                self.faiss_retriever = vector_store.as_retriever(
                    search_kwargs={"k": 10}
                )
            else:
                raise FileNotFoundError(f"FAISS Index not found at {Config.FAISS_INDEX_PATH}")

            # 2. Load Keyword Index (BM25)
            if os.path.exists(Config.BM25_INDEX_PATH):
                with open(Config.BM25_INDEX_PATH, "rb") as f:
                    self.bm25_retriever = pickle.load(f)
                    # We fetch more candidates (k=10) for RRF to re-rank effectively
                    self.bm25_retriever.k = 10
            else:
                raise FileNotFoundError(f"BM25 Index not found at {Config.BM25_INDEX_PATH}")

            print("✅ Custom RRF Hybrid Retriever Loaded.")
            
        except Exception as e:
            print(f"❌ Error loading indices: {e}")
            self.faiss_retriever = None
            self.bm25_retriever = None

    def _rrf_hybrid_search(self, query: str, k: int = 4, rrf_k: int = 60) -> list[Document]:
        """
        Your Custom Reciprocal Rank Fusion Logic.
        """
        if not self.faiss_retriever or not self.bm25_retriever:
            return []

        # 1. Get results from both retrievers
        bm25_docs = self.bm25_retriever.invoke(query)
        faiss_docs = self.faiss_retriever.invoke(query)
        
        # 2. Calculate RRF scores
        doc_scores = {}
        
        # BM25 scores
        for rank, doc in enumerate(bm25_docs, 1):
            # Create a unique key based on content to dedup
            content_key = doc.page_content
            score = 1 / (rrf_k + rank)
            if content_key in doc_scores:
                doc_scores[content_key]['score'] += score
            else:
                doc_scores[content_key] = {'doc': doc, 'score': score}
        
        # FAISS scores
        for rank, doc in enumerate(faiss_docs, 1):
            content_key = doc.page_content
            score = 1 / (rrf_k + rank)
            if content_key in doc_scores:
                doc_scores[content_key]['score'] += score
            else:
                doc_scores[content_key] = {'doc': doc, 'score': score}
        
        # 3. Sort and return top k
        sorted_docs = sorted(doc_scores.values(), key=lambda x: x['score'], reverse=True)
        return [item['doc'] for item in sorted_docs[:k]]

    def retrieve(self, query: str) -> str:
        """
        Public method to get formatted context string for the LLM.
        """
        if not self.faiss_retriever:
            return ""

        # Perform Custom RRF Search
        # We use the K defined in Config
        docs = self._rrf_hybrid_search(query, k=Config.HYBRID_SEARCH_K)
        
        if not docs:
            return ""

        # Format Documents into a single Context String
        # We format it nicely so the LLM knows the Source
        context_text = "\n\n".join(
            [f"[Source: {d.metadata.get('source', 'unknown')}] {d.metadata.get('answer_content', d.page_content)}" 
             for d in docs]
        )
        
        return context_text

# Initialize global instance
retriever_service = RetrieverService()