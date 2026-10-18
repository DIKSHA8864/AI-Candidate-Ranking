from datetime import datetime

def calculate_score(candidate, semantic_score):

    score = semantic_score * 60

    profile = candidate["profile"]

    # Experience

    exp = profile.get(
        "years_of_experience",
        0
    )

    if 5 <= exp <= 9:
        score += 15

    # Open to work

    signals = candidate.get(
        "redrob_signals",
        {}
    )

    if signals.get(
        "open_to_work_flag",
        False
    ):
        score += 5

    # Recruiter response

    response_rate = signals.get(
        "recruiter_response_rate",
        0
    )

    score += response_rate * 10

    # Profile completeness

    score += (
        signals.get(
            "profile_completeness_score",
            0
        ) / 100
    ) * 5

    # Recently active

    try:

        last_active = datetime.strptime(
            signals.get(
                "last_active_date"
            ),
            "%Y-%m-%d"
        )

        days = (
            datetime.now() -
            last_active
        ).days

        if days < 30:
            score += 5

    except:
        pass

    # Retrieval / ranking keywords

    keywords = [
        "retrieval",
        "ranking",
        "recommendation",
        "vector",
        "embedding",
        "faiss",
        "milvus",
        "pinecone",
        "search"
    ]

    text = str(candidate).lower()

    matches = sum(
        1 for k in keywords
        if k in text
    )

    score += matches

    return score