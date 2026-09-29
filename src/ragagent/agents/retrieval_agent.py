"""
The core RAG agent: retrieves relevant context from Chroma, then
generates an answer via ChatAnthropic (LangChain's Anthropic chat model).

Using ChatAnthropic instead of the raw anthropic SDK means this call is
automatically picked up by LangSmith tracing (when LANGSMITH_TRACING=true)
with no extra instrumentation code.
"""
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from ragagent.agents.base_agent import BaseAgent
from ragagent.observability.retry import llm_retry
from ragagent.retrieval.retriever import Retriever, RetrievedChunk
from ragagent.config import settings

SYSTEM_PROMPT = (
    "You are RagAgent, a helpful assistant that answers questions using "
    "retrieved context from the user's own documents.\n\n"
    "Rules:\n"
    "- Only answer using the provided context; if the answer isn't in the "
    "context, say so explicitly.\n"
    "- Cite the source document for any claim you make.\n"
    "- Be concise and direct."
)


class RetrievalAgent(BaseAgent):
    name = "retrieval_agent"

    def __init__(self, retriever: Retriever | None = None, llm: ChatAnthropic | None = None):
        self.retriever = retriever or Retriever()
        self.llm = llm or ChatAnthropic(
            model=settings.model_name,
            anthropic_api_key=settings.anthropic_api_key,
            max_tokens=1000,
        )

    def run(self, user_input: str, **kwargs) -> dict:
        chunks = self.retriever.retrieve(
            user_input,
            top_k=kwargs.get("top_k"),
            tenant_id=kwargs.get("tenant_id"),
        )

        if not chunks:
            return {
                "answer": "I don't have any ingested documents to answer from yet. "
                          "Run the ingest script first.",
                "sources": [],
                "confidence": 0.0,
            }

        prompt = self._build_prompt(user_input, chunks)
        response = self._invoke_llm([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])

        avg_score = sum(c.score for c in chunks) / len(chunks)
        return {
            "answer": response.content,
            "sources": sorted({c.source for c in chunks}),
            "confidence": round(avg_score, 3),
        }

    @llm_retry
    def _invoke_llm(self, messages: list[BaseMessage]):
        """
        Isolated so the retry decorator only wraps the actual network call
        to Claude — retrying is safe here (answering a question has no
        side effects), unlike e.g. the action agent's tool calls.
        """
        return self.llm.invoke(messages)

    def _build_prompt(self, question: str, chunks: list[RetrievedChunk]) -> str:
        context_text = "\n\n".join(f"[{c.source}]\n{c.text}" for c in chunks)
        return (
            f"Use the following context to answer the question.\n\n"
            f"Context:\n{context_text}\n\n"
            f"Question: {question}\n"
            f"Answer:"
        )
