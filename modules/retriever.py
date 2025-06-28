# retriever.py

import os
import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

class VectorRetriever:
    def __init__(self, index_path: str, metadata_path: str, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.index_path = index_path
        self.metadata_path = metadata_path
        self.embedding_model = SentenceTransformer(model_name)

        self.index = None
        self.knowledge_data = None
        self.embeddings = None
        self._load_index_and_metadata()

    def _load_index_and_metadata(self):
        if not os.path.exists(self.index_path):
            raise FileNotFoundError(f"FAISS index not found at {self.index_path}")
        self.index = faiss.read_index(self.index_path)

        if not os.path.exists(self.metadata_path):
            raise FileNotFoundError(f"Metadata file not found at {self.metadata_path}")
        with open(self.metadata_path, "rb") as f:
            self.knowledge_data = pickle.load(f)

    def retrieve(self, query: str, top_k: int = 3, similarity_threshold: float = 0.5):
        query_embedding = self.embedding_model.encode([query]).astype('float32')
        distances, indices = self.index.search(query_embedding, top_k)

        results = []
        for i, idx in enumerate(indices[0]):
            if 0 <= idx < len(self.knowledge_data):
                # Compute cosine similarity manually
                doc_embedding = self.index.reconstruct(int(idx)).reshape(1, -1)
                sim = cosine_similarity(query_embedding, doc_embedding)[0][0]
                if sim >= similarity_threshold:
                    results.append(self.knowledge_data[idx])

        return results
