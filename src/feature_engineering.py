def build_candidate_text(candidate):

    profile = candidate.get("profile", {})

    headline = profile.get("headline", "")
    summary = profile.get("summary", "")

    skills = " ".join(
        [s["name"] for s in candidate.get("skills", [])]
    )

    career = " ".join([
        c.get("description", "")
        for c in candidate.get("career_history", [])
    ])

    return f"""
    {headline}
    {summary}
    {skills}
    {career}
    """