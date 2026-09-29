"""
Run a small evaluation set of questions through the agent and print results.
Useful for quickly sanity-checking retrieval quality after changes.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ragagent.agents.router import AgentRouter

EVAL_QUESTIONS = [
    "What is the refund policy for digital products?",
    "How long does standard shipping take?",
    # Add more test questions here
]


def main():
    router = AgentRouter()
    for q in EVAL_QUESTIONS:
        print(f"\nQ: {q}")
        response = router.run(q)
        if not response["allowed"]:
            print(f"[Blocked] {response['reason']}")
            continue
        result = response["result"]
        print(f"A: {result.get('answer')}")
        print(f"   confidence={result.get('confidence')} sources={result.get('sources')}")


if __name__ == "__main__":
    main()
