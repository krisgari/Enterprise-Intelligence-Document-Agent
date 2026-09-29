"""
Orchestration entry point, built as a LangGraph StateGraph:

    START -> input_guardrail -> [END if blocked]
                              -> classify_intent -> {retrieval | summarize | action}
                                                  -> output_guardrail -> END

Each node is a plain function operating on a shared state dict, which
LangGraph threads through the graph. This gives you (for free, via
LangGraph + LangSmith):
- automatic tracing of every node/edge when LANGSMITH_TRACING=true
- the ability to add checkpointing/persistence later (MemorySaver etc.)
  without restructuring the agent logic
- a visual graph you can render (graph.get_graph().draw_mermaid()) for
  documentation or debugging

Local tracing (the /traces/{id} endpoint) is layered on top using our
own lightweight Tracer, so the API's trace endpoint works even without
a LangSmith account; LangSmith tracing is complementary, not required.
"""
from typing import TypedDict, Optional

from langgraph.graph import StateGraph, START, END

from ragagent.agents.retrieval_agent import RetrievalAgent
from ragagent.agents.summarize_agent import SummarizeAgent
from ragagent.agents.action_agent import ActionAgent
from ragagent.guardrails.input_guardrails import check_input
from ragagent.guardrails.output_guardrails import check_output
from ragagent.observability.tracer import tracer
from ragagent.observability.logger import logger


class RouterState(TypedDict, total=False):
    user_input: str
    trace_id: str
    allowed: bool
    reason: Optional[str]
    intent: str
    result: dict
    needs_human_review: bool


class AgentRouter:
    def __init__(self):
        self._retrieval_agent = RetrievalAgent()
        self._summarize_agent = SummarizeAgent()
        self._action_agent = ActionAgent()
        self.graph = self._build_graph()

    # --- Node implementations -------------------------------------------------

    def _input_guardrail_node(self, state: RouterState) -> RouterState:
        with tracer.span(state["trace_id"], "input_guardrail"):
            check = check_input(state["user_input"])
        if not check.allowed:
            logger.info("Input blocked by guardrails", extra={
                "trace_id": state["trace_id"], "reason": check.reason,
            })
        return {"allowed": check.allowed, "reason": check.reason}

    def _classify_intent_node(self, state: RouterState) -> RouterState:
        with tracer.span(state["trace_id"], "intent_classification"):
            intent = self._classify_intent(state["user_input"])
        return {"intent": intent}

    def _classify_intent(self, user_input: str) -> str:
        """
        Lightweight keyword-based classifier as a fast first pass.
        Swap for a small/cheap ChatAnthropic call (structured output)
        if you need more robust classification than keywords allow.
        """
        lowered = user_input.lower()
        if any(w in lowered for w in ("summarize", "summary", "tl;dr")):
            return "summarize"
        if any(w in lowered for w in (
            "ticket", "schedule", "book an appointment", "update record", "create a ticket",
        )):
            return "action"
        return "retrieval"

    def _retrieval_node(self, state: RouterState) -> RouterState:
        with tracer.span(state["trace_id"], "agent:retrieval_agent"):
            result = self._retrieval_agent.run(state["user_input"])
        return {"result": result}

    def _summarize_node(self, state: RouterState) -> RouterState:
        with tracer.span(state["trace_id"], "agent:summarize_agent"):
            result = self._summarize_agent.run(state["user_input"])
        return {"result": result}

    def _action_node(self, state: RouterState) -> RouterState:
        with tracer.span(state["trace_id"], "agent:action_agent"):
            result = self._action_agent.run(state["user_input"])
        return {"result": result}

    def _output_guardrail_node(self, state: RouterState) -> RouterState:
        result = state.get("result", {})
        confidence = result.get("confidence", 1.0)  # non-retrieval agents default to 1.0
        has_citation = bool(result.get("sources"))
        with tracer.span(state["trace_id"], "output_guardrail"):
            check = check_output(
                answer=result.get("answer", ""),
                confidence=confidence,
                has_citation=has_citation,
            )
        return {"needs_human_review": check.needs_human_review}

    # --- Graph wiring -----------------------------------------------------

    def _route_after_input_guardrail(self, state: RouterState) -> str:
        return "classify_intent" if state["allowed"] else END

    def _route_by_intent(self, state: RouterState) -> str:
        return {
            "retrieval": "retrieval_agent",
            "summarize": "summarize_agent",
            "action": "action_agent",
        }[state["intent"]]

    def _build_graph(self):
        graph = StateGraph(RouterState)

        graph.add_node("input_guardrail", self._input_guardrail_node)
        graph.add_node("classify_intent", self._classify_intent_node)
        graph.add_node("retrieval_agent", self._retrieval_node)
        graph.add_node("summarize_agent", self._summarize_node)
        graph.add_node("action_agent", self._action_node)
        graph.add_node("output_guardrail", self._output_guardrail_node)

        graph.add_edge(START, "input_guardrail")
        graph.add_conditional_edges(
            "input_guardrail",
            self._route_after_input_guardrail,
            {"classify_intent": "classify_intent", END: END},
        )
        graph.add_conditional_edges(
            "classify_intent",
            self._route_by_intent,
            {
                "retrieval_agent": "retrieval_agent",
                "summarize_agent": "summarize_agent",
                "action_agent": "action_agent",
            },
        )
        graph.add_edge("retrieval_agent", "output_guardrail")
        graph.add_edge("summarize_agent", "output_guardrail")
        graph.add_edge("action_agent", "output_guardrail")
        graph.add_edge("output_guardrail", END)

        return graph.compile()

    # --- Public entry point -------------------------------------------------

    def run(self, user_input: str, trace_id: str | None = None, **kwargs) -> dict:
        trace = tracer.start_trace(trace_id)

        final_state = self.graph.invoke({
            "user_input": user_input,
            "trace_id": trace.trace_id,
        })

        tracer.end_trace(trace.trace_id)

        if not final_state.get("allowed", True):
            return {
                "allowed": False,
                "reason": final_state.get("reason"),
                "trace_id": trace.trace_id,
            }

        logger.info("Request completed", extra={
            "trace_id": trace.trace_id,
            "intent": final_state.get("intent"),
        })
        return {
            "allowed": True,
            "result": final_state.get("result"),
            "needs_human_review": final_state.get("needs_human_review", False),
            "trace_id": trace.trace_id,
            "intent": final_state.get("intent"),
        }
