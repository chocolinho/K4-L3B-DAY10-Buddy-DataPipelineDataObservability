from __future__ import annotations

from typing import Any

import pandas as pd

from core.utils import first_sentence, normalize_whitespace, write_json


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    """Build a stable 10-question benchmark from the clean baseline only."""
    required = {"paper_id", "title", "summary", "authors_joined", "categories_joined", "published"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Clean dataframe is missing benchmark columns: {', '.join(missing)}")

    candidates = df.copy()
    candidates["paper_id"] = candidates["paper_id"].fillna("").astype(str).str.strip()
    candidates["title"] = candidates["title"].fillna("").astype(str).map(normalize_whitespace)
    candidates["summary"] = candidates["summary"].fillna("").astype(str)
    candidates = candidates.loc[
        candidates["paper_id"].ne("") & candidates["title"].ne("") & ~candidates["title"].str.contains("'", regex=False)
    ].drop_duplicates(subset="paper_id").sort_values("paper_id", kind="stable")
    if len(candidates) < 10:
        raise ValueError("At least 10 uniquely identified papers with quotable titles are required.")

    question_types = ["summary"] * 3 + ["authors"] * 3 + ["date"] * 2 + ["categories"] * 2
    test_set: list[dict[str, Any]] = []
    for number, (question_type, (_, row)) in enumerate(zip(question_types, candidates.head(10).iterrows()), start=1):
        title = row["title"]
        if question_type == "summary":
            question = f"Summarize the paper '{title}'."
            ground_truth = first_sentence(row["summary"])
        elif question_type == "authors":
            question = f"Who authored the paper '{title}'?"
            ground_truth = normalize_whitespace(str(row["authors_joined"]))
        elif question_type == "date":
            question = f"When was the paper '{title}' published?"
            published = pd.to_datetime(row["published"], errors="coerce")
            ground_truth = published.date().isoformat() if not pd.isna(published) else ""
        else:
            question = f"Which categories are listed for the paper '{title}'?"
            ground_truth = normalize_whitespace(str(row["categories_joined"])) or "No categories listed in the source metadata."

        if not ground_truth:
            raise ValueError(f"Paper {row['paper_id']} has no {question_type} ground truth.")
        test_set.append({
            "id": f"q{number:02d}",
            "question_type": question_type,
            "question": question,
            "ground_truth": ground_truth,
            "ground_truth_doc_ids": [row["paper_id"]],
        })

    write_json(output_path, test_set)
    return test_set
