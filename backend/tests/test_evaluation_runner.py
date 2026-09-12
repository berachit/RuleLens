import pytest
import json
from pathlib import Path
from evaluation.run_eval import run_evaluation

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RESULTS_FILE = REPO_ROOT / "evaluation" / "results.json"


@pytest.mark.asyncio
async def test_canonical_evaluation_benchmark():
    """Executes the full evaluation suite and verifies benchmark criteria."""
    summary = await run_evaluation()

    assert summary["total_questions"] == 48
    assert summary["overall_status_accuracy_pct"] >= 90.0
    assert summary["answerable_accuracy_pct"] >= 95.0
    assert summary["refusal_accuracy_pct"] >= 90.0
    assert summary["contradiction_accuracy_pct"] == 100.0
    assert summary["citation_provenance_accuracy_pct"] >= 90.0

    # Ensure machine readable results file exists and matches
    assert RESULTS_FILE.exists()
    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["total_questions"] == 48
