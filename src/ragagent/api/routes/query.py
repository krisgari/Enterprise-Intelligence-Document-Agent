"""
POST /query — the main entry point for asking the agent a question
or requesting an action.
"""
from fastapi import APIRouter

from ragagent.api.schemas import QueryRequest, QueryResponse
from ragagent.agents.router import AgentRouter

router = APIRouter()
_agent_router = AgentRouter()


@router.post("/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    response = _agent_router.run(request.query, session_id=request.session_id)
    return QueryResponse(
        allowed=response["allowed"],
        result=response.get("result"),
        reason=response.get("reason"),
        trace_id=response["trace_id"],
        intent=response.get("intent"),
    )
