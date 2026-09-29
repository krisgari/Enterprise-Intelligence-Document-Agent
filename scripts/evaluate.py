"""
Real eval harness: runs a labeled query set through the full agent graph
and scores it against expectations, rather than just eyeballing output.

For each labeled query this checks:
- intent routing: did the classifier pick the expected agent?
- guardrail behavior: did an expected-to-be-blocked input actually get blocked?
- answer quality (proxy): does the answer contain the expected keywords?
  (a simple substring/recall check, not semantic — cheap, deterministic,
  and good enough to catch a regression; swap for an LLM-graded rubric or
  a real ragas/deepeval integration for a closer measure of correctness)
- latency: wall-clock time per query, so a regression in retrieval or
  prompt size shows up here before a user notices it

Run with: python scripts/evaluate.py
Add --include-actions to also execute action-intent queries (these have
real side effects, e.g. creating a ticket, so they're skipped by default).
Add --output results.json to save a machine-readable report (useful for
wiring this into CI and diffing runs over time).

This intentionally stays dependency-light (no ragas/deepeval) so it runs
anywhere this project already runs; the docstring above notes where a
heavier eval framework would plug in for a closer semantic-correctness
measure.
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ragagent.agents.router import AgentRouter

EVAL_FILE = Path(__file__).parent.parent / "data" / "eval" / "queries.json"


def load_eval_set() -> list[dict]:
    with open(EVAL_FILE) as f:
        return json.load(f)


def score_one(router: AgentRouter, case: dict, include_actions: bool) -> dict:
    if case.get("skip_execution") and not include_actions:
        return {"id": case["id"], "query": case["query"], "skipped": True}

    start = time.perf_counter()
    response = router.run(case["query"])
    latency_ms = round((time.perf_counter() - start) * 1000, 1)

    result = {
        "id": case["id"],
        "query": case["query"],
        "latency_ms": latency_ms,
        "skipped": False,
    }

    if case.get("expect_blocked"):
        result["pass"] = response["allowed"] is False
        result["detail"] = "blocked as expected" if result["pass"] else \
            f"expected blocked, got allowed={response['allowed']}"
        return result

    if not response["allowed"]:
        result["pass"] = False
        result["detail"] = f"unexpectedly blocked: {response.get('reason')}"
        return result

    intent_ok = response.get("intent") == case["expected_intent"]

    answer = (response.get("result") or {}).get("answer", "") or ""
    answer_lower = answer.lower()

    if case["expected_intent"] == "action":
        # A keyword check on prose isn't meaningful here — an action's
        # success is whether a real tool call actually happened, so check
        # for the concrete artifact it produces (a ticket ID) rather than
        # just trusting that intent classification routed correctly.
        action_ok = bool(re.search(r"TICKET-\d+", answer))
        result["intent"] = response.get("intent")
        result["expected_intent"] = case["expected_intent"]
        result["pass"] = intent_ok and action_ok
        reasons = []
        if not intent_ok:
            reasons.append(f"intent {response.get('intent')!r} != expected {case['expected_intent']!r}")
        if not action_ok:
            reasons.append("no TICKET-<id> found in answer — the MCP tool call may not have actually run")
        result["detail"] = "; ".join(reasons) if reasons else "ok (ticket id found)"
        return result

    expected_keywords = case.get("expected_keywords", [])
    found = [kw for kw in expected_keywords if kw.lower() in answer_lower]
    missing = [kw for kw in expected_keywords if kw not in found]
    keyword_recall = len(found) / len(expected_keywords) if expected_keywords else 1.0

    result["intent"] = response.get("intent")
    result["expected_intent"] = case["expected_intent"]
    result["keyword_recall"] = round(keyword_recall, 2)
    result["missing_keywords"] = missing
    result["pass"] = intent_ok and keyword_recall == 1.0
    if not result["pass"]:
        reasons = []
        if not intent_ok:
            reasons.append(f"intent {response.get('intent')!r} != expected {case['expected_intent']!r}")
        if missing:
            reasons.append(f"missing keywords: {missing}")
        result["detail"] = "; ".join(reasons)
    else:
        result["detail"] = "ok"

    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-actions", action="store_true",
                         help="Also execute action-intent queries (has real side effects).")
    parser.add_argument("--output", default=None, help="Optional path to write a JSON report to.")
    args = parser.parse_args()

    cases = load_eval_set()
    router = AgentRouter()
    results = [score_one(router, case, args.include_actions) for case in cases]

    ran = [r for r in results if not r["skipped"]]
    passed = [r for r in ran if r.get("pass")]
    avg_latency = round(sum(r["latency_ms"] for r in ran) / len(ran), 1) if ran else 0.0

    print(f"{'ID':<5} {'PASS':<6} {'LATENCY':<10} DETAIL")
    for r in results:
        if r["skipped"]:
            print(f"{r['id']:<5} {'SKIP':<6} {'-':<10} (skip_execution=true, use --include-actions)")
            continue
        status = "PASS" if r["pass"] else "FAIL"
        print(f"{r['id']:<5} {status:<6} {r['latency_ms']:<10} {r['detail']}")

    print()
    print(f"{len(passed)}/{len(ran)} passed ({len(results) - len(ran)} skipped), "
          f"avg latency {avg_latency}ms")

    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Report written to {args.output}")

    if len(passed) < len(ran):
        sys.exit(1)


if __name__ == "__main__":
    main()
