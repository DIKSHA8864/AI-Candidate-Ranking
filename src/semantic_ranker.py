from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

def semantic_scores(jd_text, candidate_texts):

    jd_emb = model.encode([jd_text])

    cand_emb = model.encode(
        candidate_texts,
        show_progress_bar=True
    )

    scores = cosine_similarity(
        jd_emb,
        cand_emb
    )[0]

    return scores