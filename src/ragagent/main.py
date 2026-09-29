"""
Simple CLI entry point for RagAgent.
Run with: python -m ragagent.main
"""
from ragagent.agents.router import AgentRouter


def main():
    router = AgentRouter()
    print("RagAgent ready. Type 'exit' to quit.")
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break

        response = router.run(user_input)
        if not response["allowed"]:
            print(f"\n[Blocked by guardrails] {response['reason']}")
            continue

        result = response["result"]
        print(f"\nRagAgent ({response['intent']}): {result.get('answer')}")
        if result.get("sources"):
            print(f"Sources: {', '.join(result['sources'])}")
        if response.get("needs_human_review"):
            print("[Flagged for human review]")


if __name__ == "__main__":
    main()
