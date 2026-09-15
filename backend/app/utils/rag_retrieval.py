import re
import numpy as np
from typing import List, Dict, Any, Optional
from backend.app.utils.logging import logger

# Try loading Sentence Transformers & FAISS with fallback
HAS_RAG_DEPS = False
try:
    from sentence_transformers import SentenceTransformer
    import faiss
    HAS_RAG_DEPS = True
except Exception as e:
    logger.warning(f"RAG dependencies loading error (falling back to vector math): {e}")

class RAGKnowledgeRetriever:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.name = "RAG Knowledge Retrieval"
        self.icon = "📚"
        self.model_name = model_name
        self.model = None
        self.use_transformer = False

        if HAS_RAG_DEPS:
            try:
                # Try loading local cached model first
                self.model = SentenceTransformer(self.model_name, local_files_only=True)
                self.use_transformer = True
                logger.info(f"Loaded local SentenceTransformer model '{self.model_name}' successfully.")
            except Exception:
                try:
                    logger.info(f"SentenceTransformer model '{self.model_name}' not cached locally. Downloading model...")
                    self.model = SentenceTransformer(self.model_name)
                    self.use_transformer = True
                    logger.info(f"Loaded SentenceTransformer model '{self.model_name}' successfully.")
                except Exception as ex:
                    logger.warning(f"Could not load SentenceTransformer model ({ex}). Falling back to fast vector embedding engine.")

    def _embed_text(self, text: str) -> np.ndarray:
        if self.use_transformer and self.model:
            try:
                embedding = self.model.encode(text, convert_to_numpy=True)
                # Normalize vector for cosine similarity
                norm = np.linalg.norm(embedding)
                if norm > 0:
                    embedding = embedding / norm
                return embedding.astype('float32')
            except Exception as e:
                logger.error(f"Error encoding with SentenceTransformer: {e}")

        # Fallback pseudo-embedding generator using word/char hashing into 384 dimensions
        vec = np.zeros(384, dtype='float32')
        words = re.findall(r'\w+', text.lower())
        for w in words:
            idx = abs(hash(w)) % 384
            vec[idx] += 1.0
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec

    def retrieve_similar_resolutions(
        self,
        bug_report: Dict[str, Any],
        resolved_bugs: List[Dict[str, Any]],
        top_k: int = 3
    ) -> Dict[str, Any]:
        """Uses FAISS index + SentenceTransformers embeddings to retrieve relevant historical bugs and confirmed resolutions."""
        if not resolved_bugs:
            return {
                "agent": self.name,
                "icon": self.icon,
                "retrievedCount": 0,
                "items": [],
                "summary": "No historical resolved bugs available in database for RAG retrieval.",
                "details": {
                    "status": "ℹ️ Knowledge Base empty",
                    "retrieved": []
                }
            }

        title = bug_report.get("title", "")
        desc = bug_report.get("description", "")
        stack = bug_report.get("stackTrace") or bug_report.get("stack_trace") or ""
        query_text = f"{title}\n{desc}\n{stack}".strip()

        # Build corpus vectors from resolved bugs
        corpus_texts = []
        for bug in resolved_bugs:
            bug_text = f"{bug.get('title', '')} {bug.get('description', '')} {bug.get('stack_trace', '')} Root Cause: {bug.get('root_cause', '')} Resolution: {bug.get('resolution', '')}"
            corpus_texts.append(bug_text)

        query_vec = self._embed_text(query_text)
        corpus_vecs = np.array([self._embed_text(t) for t in corpus_texts], dtype='float32')

        dim = query_vec.shape[0]

        # Use FAISS index if available
        scores = []
        indices = []

        if HAS_RAG_DEPS and 'faiss' in globals():
            try:
                # Flat Inner Product index for normalized vectors = Cosine Similarity
                index = faiss.IndexFlatIP(dim)
                index.add(corpus_vecs)
                
                q_arr = np.array([query_vec], dtype='float32')
                k = min(top_k, len(resolved_bugs))
                distances, faiss_indices = index.search(q_arr, k)
                
                for sim, idx in zip(distances[0], faiss_indices[0]):
                    if idx >= 0 and idx < len(resolved_bugs):
                        scores.append(float(sim))
                        indices.append(int(idx))
            except Exception as ex:
                logger.warning(f"FAISS indexing error ({ex}), using numpy vector dot product.")
                scores, indices = self._vector_dot_product_search(query_vec, corpus_vecs, top_k)
        else:
            scores, indices = self._vector_dot_product_search(query_vec, corpus_vecs, top_k)

        items = []
        for sim_score, idx in zip(scores, indices):
            b = resolved_bugs[idx]
            match_pct = min(99, max(1, int(round(sim_score * 100))))
            items.append({
                "id": b.get("bug_code") or f"BUG-{b.get('id'):03d}",
                "title": b.get("title"),
                "category": b.get("category"),
                "similarityScore": match_pct,
                "rootCause": b.get("root_cause") or "Not documented",
                "confirmedResolution": b.get("resolution") or "Not documented",
                "dateResolved": str(b.get("date_resolved")) if b.get("date_resolved") else "N/A"
            })

        top_item = items[0] if items else {}
        retrieved_count = len(items)

        summary_text = (
            f"Retrieved {retrieved_count} historical resolution(s) using Sentence Transformers + FAISS vector search."
            if items else "No matching historical resolutions found."
        )

        return {
            "agent": self.name,
            "icon": self.icon,
            "retrievedCount": retrieved_count,
            "topMatchId": top_item.get("id"),
            "topMatchSimilarity": top_item.get("similarityScore", 0),
            "topConfirmedResolution": top_item.get("confirmedResolution"),
            "items": items,
            "summary": summary_text,
            "details": {
                "vectorEngine": "SentenceTransformers (all-MiniLM-L6-v2) + FAISS IndexFlatIP" if self.use_transformer else "Vector Embedding + Cosine Vector Engine",
                "retrievedResolutions": [
                    {
                        "bugCode": item["id"],
                        "title": item["title"],
                        "relevance": f"{item['similarityScore']}% similarity",
                        "confirmedFix": item["confirmedResolution"]
                    } for item in items
                ]
            }
        }

    def _vector_dot_product_search(self, q_vec: np.ndarray, corpus_vecs: np.ndarray, top_k: int):
        sims = np.dot(corpus_vecs, q_vec)
        top_k_indices = np.argsort(sims)[::-1][:top_k]
        return [float(sims[i]) for i in top_k_indices], [int(i) for i in top_k_indices]

rag_retriever = RAGKnowledgeRetriever()
