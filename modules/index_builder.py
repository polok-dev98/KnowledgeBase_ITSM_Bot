import os
import faiss
import pickle
import pandas as pd
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

class KnowledgeEmbedder:
    def __init__(self, csv_path, embedding_model_name="all-MiniLM-L6-v2"):
        self.csv_path = csv_path
        self.embedding_model_name = embedding_model_name
        self.model = SentenceTransformer(self.embedding_model_name)
        self.index = None
        self.knowledge_data = []

    def process_csv(self):
        print(f"🔍 Loading CSV: {self.csv_path}")
        df = pd.read_csv(self.csv_path)

        # Drop rows with missing required fields
        df = df.dropna(subset=["ki_topic", "ki_text"])

        # Fill alt/bad text if missing (so string ops don't break)
        df["alt_ki_text"] = df["alt_ki_text"].fillna("")
        df["bad_ki_text"] = df["bad_ki_text"].fillna("")

        # Combine columns into one string per row
        df["combined_text"] = (
            df["ki_topic"].str.strip() + ". " +
            df["ki_text"].str.strip() + " ALT: " +
            df["alt_ki_text"].str.strip() + " BAD: " +
            df["bad_ki_text"].str.strip()
        )

        # Drop duplicates
        df = df.drop_duplicates(subset="combined_text").reset_index(drop=True)

        # Prepare for embedding
        texts = df["combined_text"].tolist()
        metadata = df[["ki_topic", "ki_text"]].to_dict(orient="records")

        print(f"🔢 Generating embeddings for {len(texts)} entries...")
        embeddings = self.model.encode(texts, show_progress_bar=True)

        # Build FAISS index
        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dim)
        self.index.add(embeddings)

        # Save metadata for retrieval
        self.knowledge_data = metadata
        print("✅ Embedding complete.")

    def save_to_disk(self, index_path="vector_store/kb_index.faiss", metadata_path="vector_store/kb_metadata.pkl"):
        os.makedirs(os.path.dirname(index_path), exist_ok=True)

        faiss.write_index(self.index, index_path)
        print(f"💾 Saved FAISS index to: {index_path}")

        with open(metadata_path, "wb") as f:
            pickle.dump(self.knowledge_data, f)
        print(f"💾 Saved metadata to: {metadata_path}")


if __name__ == "__main__":
    load_dotenv()
    embedder = KnowledgeEmbedder(csv_path="data/synthetic_knowledge_items.csv")
    embedder.process_csv()
    embedder.save_to_disk()
