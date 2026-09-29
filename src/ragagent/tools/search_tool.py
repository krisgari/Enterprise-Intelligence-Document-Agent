"""
Example tool: a web search function the agent can call.
Replace the body with a real search API integration (e.g. Tavily, SerpAPI, Bing).
"""


def web_search(query: str, max_results: int = 5) -> list[dict]:
    """
    Search the web and return a list of {title, url, snippet} dicts.
    """
    raise NotImplementedError("Wire up a real search API here")
