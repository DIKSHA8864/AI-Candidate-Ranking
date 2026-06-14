import json

def load_candidates(file_path):
    candidates = []

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            candidates.append(json.loads(line))

    return candidates