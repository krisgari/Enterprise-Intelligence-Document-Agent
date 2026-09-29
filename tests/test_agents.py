from ragagent.agents.retrieval_agent import RetrievalAgent
from ragagent.retrieval.retriever import RetrievedChunk


def test_retrieval_agent_instantiates():
    agent = RetrievalAgent()
    assert agent.name == "retrieval_agent"


def test_build_prompt_includes_question_and_context():
    agent = RetrievalAgent()
    chunks = [RetrievedChunk(text="X is a thing.", source="doc1.md", score=0.9)]
    prompt = agent._build_prompt("What is X?", chunks)
    assert "What is X?" in prompt
    assert "X is a thing." in prompt
    assert "doc1.md" in prompt
