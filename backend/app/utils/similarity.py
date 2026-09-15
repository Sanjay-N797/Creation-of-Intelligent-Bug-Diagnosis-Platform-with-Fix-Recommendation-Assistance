import re
import math
from typing import List, Dict

def tokenize(text: str) -> List[str]:
    """Tokenize text into lowercased words with length > 2."""
    if not text:
        return []
    clean_text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text.lower())
    return [word for word in clean_text.split() if len(word) > 2]

def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate cosine similarity between two text strings."""
    if not text1 or not text2:
        return 0.0

    tokens1 = tokenize(text1)
    tokens2 = tokenize(text2)

    if not tokens1 or not tokens2:
        return 0.0

    freq1: Dict[str, int] = {}
    freq2: Dict[str, int] = {}

    for t in tokens1:
        freq1[t] = freq1.get(t, 0) + 1

    for t in tokens2:
        freq2[t] = freq2.get(t, 0) + 1

    all_tokens = set(freq1.keys()).union(set(freq2.keys()))
    
    dot_product = 0.0
    mag1 = 0.0
    mag2 = 0.0

    for token in all_tokens:
        v1 = freq1.get(token, 0)
        v2 = freq2.get(token, 0)
        dot_product += v1 * v2
        mag1 += v1 * v1
        mag2 += v2 * v2

    mag1 = math.sqrt(mag1)
    mag2 = math.sqrt(mag2)

    if mag1 == 0 or mag2 == 0:
        return 0.0

    return dot_product / (mag1 * mag2)

def compute_tfidf_similarity(query: str, corpus: List[str]) -> List[float]:
    """Computes TF-IDF vector representations and Cosine Similarity scores between query and corpus."""
    if not query or not corpus:
        return [0.0] * len(corpus)

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        vectorizer = TfidfVectorizer(stop_words='english', token_pattern=r'(?u)\b\w+\b')
        all_documents = [query] + corpus
        tfidf_matrix = vectorizer.fit_transform(all_documents)
        
        query_vec = tfidf_matrix[0:1]
        corpus_vecs = tfidf_matrix[1:]

        sims = cosine_similarity(query_vec, corpus_vecs)[0]
        return [float(s) for s in sims]
    except Exception:
        # Fallback to token cosine similarity
        return [calculate_similarity(query, doc) for doc in corpus]

