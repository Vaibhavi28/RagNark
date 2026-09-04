import json
import random
from pathlib import Path
import numpy as np
import pytest
from sentence_transformers import SentenceTransformer

FILTERED_PATH = Path("backend/knowledge_base/raw_data/hackaprompt/filtered_candidates.jsonl")
REPORT_PATH = Path("backend/knowledge_base/raw_data/hackaprompt/filter_report.json")


def test_filtered_candidates_created_and_fields_valid():
    """Test filtered_candidates.jsonl is created and every line has all required fields."""
    assert FILTERED_PATH.exists(), f"File {FILTERED_PATH} does not exist"

    required_fields = {
        "candidate_id",
        "source",
        "original_row_index",
        "prompt_text",
        "max_anchor_similarity",
        "closest_anchor"
    }

    count = 0
    with open(FILTERED_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            count += 1
            for rf in required_fields:
                assert rf in item, f"Missing field '{rf}' in candidate #{item.get('candidate_id')}"
            assert item["source"] == "HackAPrompt"
            assert isinstance(item["candidate_id"], int)
            assert isinstance(item["max_anchor_similarity"], (float, int))

    assert count > 0, "filtered_candidates.jsonl has 0 candidates"


def test_filter_report_created_and_contains_all_fields():
    """Test filter_report.json is created and contains all required fields."""
    assert REPORT_PATH.exists(), f"File {REPORT_PATH} does not exist"

    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        report = json.load(f)

    required_fields = [
        "total_rows_input",
        "rows_after_keyword_filter",
        "rows_after_embedding_filter",
        "unique_rows_after_dedup",
        "similarity_threshold_relevance",
        "similarity_threshold_dedup",
        "embedding_model",
        "processing_date",
        "malformed_lines_skipped"
    ]
    for rf in required_fields:
        assert rf in report, f"Missing field '{rf}' in filter_report.json"


def test_monotonic_filtering_counts():
    """Test rows_after_embedding_filter <= rows_after_keyword_filter <= total_rows_input."""
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        report = json.load(f)

    assert report["rows_after_keyword_filter"] <= report["total_rows_input"]
    assert report["rows_after_embedding_filter"] <= report["rows_after_keyword_filter"]


def test_deduplication_reduction_count():
    """Test unique_rows_after_dedup <= rows_after_embedding_filter."""
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        report = json.load(f)

    assert report["unique_rows_after_dedup"] <= report["rows_after_embedding_filter"]


def test_no_duplicate_pairs_above_threshold():
    """Test that no two candidates in a random sample of 50 pairs have cosine similarity >= 0.92."""
    candidates = []
    with open(FILTERED_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                candidates.append(json.loads(line))

    assert len(candidates) > 0, "No candidates found"

    # If there are fewer than 2 candidates, test trivially passes
    if len(candidates) < 2:
        return

    # Select random sample of up to 50 distinct pairs (i, j) where i != j
    all_pairs = [(i, j) for i in range(len(candidates)) for j in range(i + 1, len(candidates))]
    sample_pairs = random.sample(all_pairs, min(50, len(all_pairs)))

    indices_needed = set()
    for i, j in sample_pairs:
        indices_needed.add(i)
        indices_needed.add(j)

    sorted_indices = sorted(indices_needed)
    index_map = {orig: idx for idx, orig in enumerate(sorted_indices)}
    sample_texts = [candidates[i]["prompt_text"] for i in sorted_indices]

    model = SentenceTransformer("all-MiniLM-L6-v2")
    sample_embeddings = model.encode(sample_texts, normalize_embeddings=True)

    for i, j in sample_pairs:
        idx_i = index_map[i]
        idx_j = index_map[j]
        cos_sim = float(np.dot(sample_embeddings[idx_i], sample_embeddings[idx_j]))
        assert cos_sim < 0.92, (
            f"Candidate {candidates[i]['candidate_id']} and {candidates[j]['candidate_id']} "
            f"have cosine similarity {cos_sim:.4f} >= 0.92"
        )
