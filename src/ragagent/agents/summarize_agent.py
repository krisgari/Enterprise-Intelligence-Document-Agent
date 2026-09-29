"""
Agent specialized in summarization tasks (e.g. "summarize this policy",
"give me the key points from these documents").
"""
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage

from ragagent.agents.base_agent import BaseAgent
from ragagent.retrieval.retriever import Retriever
from ragagent.config import settings

SUMMARY_PROMPT_TEMPLATE = (
    "Summarize the following content in plain language, in no more than "
    "5 bullet points. Do not add information that isn't present in the text.\n\n"
    "Content:\n{context}\n\nSummary:"
)


class SummarizeAgent(BaseAgent):
    name = "summarize_agent"

    def __init__(self, retriever: Retriever | None = None, llm: ChatAnthropic | None = None):
        self.retriever = retriever or Retriever()
        self.llm = llm or ChatAnthropic(
            model=settings.model_name,
            anthropic_api_key=settings.anthropic_api_key,
            max_tokens=1000,
        )

    def run(self, user_input: str, **kwargs) -> dict:
        chunks = self.retriever.retrieve(user_input, top_k=kwargs.get("top_k"))
        if not chunks:
            return {"answer": "No ingested documents found to summarize.", "sources": []}

        context_text = "\n\n".join(c.text for c in chunks)
        prompt = SUMMARY_PROMPT_TEMPLATE.format(context=context_text)
        response = self.llm.invoke([HumanMessage(content=prompt)])

        return {
            "answer": response.content,
            "sources": sorted({c.source for c in chunks}),
        }
