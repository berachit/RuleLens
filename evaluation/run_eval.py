#!/usr/bin/env python
"""RuleLens Evaluation Benchmark Runner.

Executes the canonical evaluation benchmark against the RuleLens RAG engine.
Measures:
- Overall status classification accuracy (ANSWERED vs NOT_COVERED vs CONFLICT)
- Refusal accuracy on unanswerable questions
- Contradiction detection rate
- Citation accuracy and provenance validity

Outputs machine-readable evaluation/results.json and human-readable terminal report.
"""

import sys
import json
import asyncio
import time
from pathlib import Path
from typing import Dict, Any, List

# Add backend directory to sys.path so app modules import cleanly
EVAL_DIR = Path(__file__).resolve().parent
REPO_ROOT = EVAL_DIR.parent
BACKEND_DIR = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.services.rag.engine import rag_engine

QUESTIONS_FILE = EVAL_DIR / "questions.json"
RESULTS_FILE = EVAL_DIR / "results.json"


async def run_evaluation() -> Dict[str, Any]:
    if not QUESTIONS_FILE.exists():
        print(f"Error: Questions file not found at {QUESTIONS_FILE}")
        sys.exit(1)

    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        questions: List[Dict[str, Any]] = json.load(f)

    print("=" * 80)
    print(f"RuleLens Canonical Evaluation Benchmark — {len(questions)} Questions")
    print("=" * 80)

    results = []
    category_counts = {"answerable": 0, "unanswerable": 0, "contradiction": 0}
    category_passed = {"answerable": 0, "unanswerable": 0, "contradiction": 0}
    citation_passed_count = 0
    total_evaluated = 0

    start_time = time.time()

    for item in questions:
        q_id = item["id"]
        category = item["category"]
        query = item["question"]
        expected_status = item["expected_status"]
        expected_sources = item.get("expected_sources", [])

        category_counts[category] += 1
        total_evaluated += 1

        # Run query through RAG engine
        res = await rag_engine.process_query(query)
        actual_status = res["status"]
        sources = res.get("sources", [])

        # Check status match
        status_correct = (actual_status == expected_status)
        if status_correct:
            category_passed[category] += 1

        # Check citations
        citation_correct = False
        if expected_status in ["ANSWERED", "CONFLICT"]:
            if len(sources) > 0:
                # Check that every source contains required provenance
                has_provenance = all(
                    s.get("document") and s.get("page", 0) > 0 and s.get("chunk_id")
                    for s in sources
                )
                citation_correct = has_provenance
        elif expected_status == "NOT_COVERED":
            # For unanswerable, sources should be empty
            citation_correct = (len(sources) == 0)

        if citation_correct:
            citation_passed_count += 1

        eval_record = {
            "id": q_id,
            "category": category,
            "question": query,
            "expected_status": expected_status,
            "actual_status": actual_status,
            "status_correct": status_correct,
            "citation_correct": citation_correct,
            "sources_count": len(sources),
            "sources": sources,
            "answer_preview": res["answer"][:160] + "...",
        }
        results.append(eval_record)

        # Print live status
        symbol = "PASS" if status_correct else "FAIL"
        print(f"[{symbol:<4}] {q_id:<4} | {category:<14} | Exp: {expected_status:<11} | Act: {actual_status:<11} | Citations: {len(sources)}")

    total_duration = round(time.time() - start_time, 2)
    overall_status_accuracy = round((sum(category_passed.values()) / total_evaluated) * 100, 2)
    refusal_accuracy = round((category_passed["unanswerable"] / category_counts["unanswerable"]) * 100, 2)
    contradiction_accuracy = round((category_passed["contradiction"] / category_counts["contradiction"]) * 100, 2)
    answerable_accuracy = round((category_passed["answerable"] / category_counts["answerable"]) * 100, 2)
    citation_accuracy = round((citation_passed_count / total_evaluated) * 100, 2)

    summary = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_questions": total_evaluated,
        "duration_seconds": total_duration,
        "overall_status_accuracy_pct": overall_status_accuracy,
        "answerable_accuracy_pct": answerable_accuracy,
        "refusal_accuracy_pct": refusal_accuracy,
        "contradiction_accuracy_pct": contradiction_accuracy,
        "citation_provenance_accuracy_pct": citation_accuracy,
        "breakdown": {
            "answerable": {"total": category_counts["answerable"], "passed": category_passed["answerable"]},
            "unanswerable": {"total": category_counts["unanswerable"], "passed": category_passed["unanswerable"]},
            "contradiction": {"total": category_counts["contradiction"], "passed": category_passed["contradiction"]},
        },
        "results": results,
    }

    # Save to evaluation/results.json
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 80)
    print("EVALUATION BENCHMARK SUMMARY")
    print("=" * 80)
    print(f"Total Questions Evaluated:          {total_evaluated}")
    print(f"Execution Duration:                 {total_duration}s")
    print(f"Overall Status Classification:      {overall_status_accuracy}% ({sum(category_passed.values())}/{total_evaluated})")
    print(f"Answerable Accuracy:                {answerable_accuracy}% ({category_passed['answerable']}/{category_counts['answerable']})")
    print(f"Refusal Accuracy (NOT_COVERED):     {refusal_accuracy}% ({category_passed['unanswerable']}/{category_counts['unanswerable']})")
    print(f"Contradiction Detection (CONFLICT): {contradiction_accuracy}% ({category_passed['contradiction']}/{category_counts['contradiction']})")
    print(f"Citation Provenance Validity:       {citation_accuracy}% ({citation_passed_count}/{total_evaluated})")
    print("=" * 80)
    print(f"Detailed machine-readable output written to: {RESULTS_FILE}\n")

    return summary


if __name__ == "__main__":
    asyncio.run(run_evaluation())
