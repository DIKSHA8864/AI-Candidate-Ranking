import pandas as pd

# Read your existing ranked file
df = pd.read_csv("output/ranked_candidates.csv")

# Sort by score
df = df.sort_values("score", ascending=False).reset_index(drop=True)

# Add rank column
df["rank"] = df.index + 1

# Add reasoning column
df["reasoning"] = (
    "Selected based on semantic job match, relevant experience, skills alignment, and candidate activity signals."
)

# Arrange columns in required order
df = df[["candidate_id", "rank", "score", "reasoning"]]

# Save final submission
df.to_csv("final_submission.csv", index=False)

print("✅ Final submission created successfully!")
print(df.head())