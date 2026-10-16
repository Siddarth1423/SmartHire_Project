"""Resume/job matching. Uses Sentence Transformers + FAISS when installed,
and a lightweight token-overlap fallback otherwise."""
import re

def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z][a-zA-Z0-9+#.-]{1,}", (text or "").lower()))

def match_score(resume_text: str, job_text: str) -> float:
    resume_text, job_text = resume_text or "", job_text or ""
    if not resume_text.strip() or not job_text.strip():
        return 0.0
    try:
        from sentence_transformers import SentenceTransformer
        import faiss
        import numpy as np
        model = SentenceTransformer("all-MiniLM-L6-v2")
        vectors = model.encode([resume_text, job_text], normalize_embeddings=True)
        index = faiss.IndexFlatIP(vectors.shape[1])
        index.add(np.asarray([vectors[1]], dtype="float32"))
        scores, _ = index.search(np.asarray([vectors[0]], dtype="float32"), 1)
        return round(max(0.0, min(1.0, float(scores[0][0]))) * 100, 1)
    except Exception:
        a, b = _tokens(resume_text), _tokens(job_text)
        if not a or not b:
            return 0.0
        # Dice similarity is intentionally transparent as a no-model fallback.
        return round(200 * len(a & b) / (len(a) + len(b)), 1)
