# RagAgent

An enterprise document intelligence agent, built on real production tooling:

- **[LangGraph](https://langchain-ai.github.io/langgraph/)** — orchestration as a real state graph (not hand-rolled if/else routing)
- **[ChromaDB](https://www.trychroma.com/)** — vector store, via `langchain-chroma`, running as its own service
- **[LangSmith](https://smith.langchain.com/)** — tracing/observability, automatic once enabled, no per-call instrumentation
- **MCP** (Model Context Protocol), via `langchain-mcp-adapters` — real external tool/action execution
- **FastAPI** — the serving layer
- Custom **guardrails** — input (PII/prompt-injection) and output (confidence/citation/scope) checks, framework-agnostic

## Architecture

```
Client → FastAPI → LangGraph:

  START
    │
    ▼
  input_guardrail  ──(blocked)──▶ END
    │ (allowed)
    ▼
  classify_intent
    │
    ├──▶ retrieval_agent  (ChatAnthropic + Chroma RAG)
    ├──▶ summarize_agent  (ChatAnthropic + Chroma RAG)
    └──▶ action_agent     (LangGraph create_react_agent + MCP tools)
    │
    ▼
  output_guardrail (confidence / citation / scope checks)
    │
    ▼
   END
```

Every `ChatAnthropic` call inside the graph is automatically traced to
LangSmith when tracing is enabled — no manual span code needed for LLM
calls. A lightweight local `Tracer` additionally records a span per
graph node, so `GET /traces/{trace_id}` works even without a LangSmith
account; the two are complementary, not redundant.

## Structure

- `src/ragagent/api/` — FastAPI app and routes (`/query`, `/ingest`, `/feedback`, `/traces/{id}`)
- `src/ragagent/agents/router.py` — **the LangGraph StateGraph**: node definitions, conditional routing, the whole orchestration
- `src/ragagent/agents/retrieval_agent.py`, `summarize_agent.py` — `ChatAnthropic`-based agents, each pulling context via the `Retriever`
- `src/ragagent/agents/action_agent.py` — `langgraph.prebuilt.create_react_agent` wired to MCP tools
- `src/ragagent/retrieval/vectorstore.py` — Chroma vectorstore factory (server or embedded mode via config)
- `src/ragagent/retrieval/embedder.py` — `HuggingFaceEmbeddings` wrapper (local model, no external API key)
- `src/ragagent/retrieval/retriever.py` — thin wrapper over Chroma similarity search
- `src/ragagent/mcp/client.py` — `MultiServerMCPClient` wrapper, converts MCP tools into LangChain tools
- `src/ragagent/mcp/servers.py` — re-exports the MCP server config from `settings` (single source of truth)
- `mcp_servers/ticketing_server.py` — a real, standalone MCP server (built with `mcp.server.fastmcp.FastMCP`) exposing a small ticketing system; registered by default so `action_agent` works out of the box
- `src/ragagent/guardrails/` — input validation (PII, prompt injection) and output validation (confidence, citations, scope) — plain Python, no framework dependency
- `src/ragagent/observability/` — local `Tracer`/structured logger, plus `langsmith_setup.py` to enable LangSmith via env vars
- `src/ragagent/skills/` — optional reusable capabilities (currently stubs; `summarize_agent` has its own inlined logic and doesn't require these)
- `src/ragagent/tools/` — single-purpose callable tools (non-MCP, e.g. web search)
- `dashboard/index.html` — minimal standalone page to inspect a trace by ID
- `data/` — raw documents (`data/raw/`) and Chroma's embedded persistence dir if running without the Chroma service
- `docker-compose.yml` — runs the API **and** a real Chroma server together

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env: add ANTHROPIC_API_KEY, optionally LANGSMITH_API_KEY
```

`sentence-transformers` downloads a small local embedding model
(~90MB, `all-MiniLM-L6-v2`) on first use — needs internet once, then
runs offline.

### Choose how Chroma runs

**Option A — Docker Compose (recommended, closer to a real deployment):**
```bash
docker-compose up
```
This runs a standalone Chroma server (`chroma` service) plus the API,
with `CHROMA_HOST`/`CHROMA_PORT` wired automatically. This is the mode
that actually reflects "vector store as its own service" rather than an
embedded library — the difference matters once you have multiple API
replicas needing to share one vector store.

**Option B — Embedded local Chroma (simplest for iterating on code):**
Leave `CHROMA_HOST` unset in `.env`. Chroma runs embedded in the API
process and persists to `CHROMA_PERSIST_DIR` (`data/vectorstore/` by default).

### Enable LangSmith tracing (optional but recommended)

Get a key at [smith.langchain.com](https://smith.langchain.com), then in `.env`:
```
LANGSMITH_API_KEY=your-key
LANGSMITH_TRACING=true
```
Every LLM call and graph node execution will show up in your LangSmith
project (`ragagent` by default) — full input/output, latency, and token
usage per step, without touching agent code.

## Usage — get a real answer end to end

A sample `data/raw/sample_policies.md` is included so you can test
immediately without your own documents.

**1. Ingest the sample documents:**
```bash
python scripts/ingest.py
```

**2. Run the API:**
```bash
cd src && uvicorn ragagent.api.app:app --reload
```

**3. Ask a question:**
```bash
curl -X POST http://localhost:8000/query -H "Content-Type: application/json" \
  -d '{"query": "What is the refund policy for digital products?"}'
```
You'll get back a real, model-generated answer grounded in the sample
doc, with `sources`, a `confidence` score, and a `trace_id`.

**4. Inspect the trace:**
```bash
curl http://localhost:8000/traces/<trace_id>
```
Or open `dashboard/index.html` in a browser (with the API running).
If LangSmith is enabled, also check your LangSmith project for the
full LLM-level trace (prompts, tokens, latency).

**5. Try a summarization request:**
```bash
curl -X POST http://localhost:8000/query -H "Content-Type: application/json" \
  -d '{"query": "Summarize the shipping policy"}'
```
The intent classifier routes this to `summarize_agent` instead of `retrieval_agent`.

## MCP is wired up with a real sample server

`mcp_servers/ticketing_server.py` is a genuine MCP server (built with
the official `mcp.server.fastmcp.FastMCP`), exposing four tools:
`create_ticket`, `get_ticket`, `list_tickets`, `update_ticket_status`.
It's already registered in `config.py`'s `mcp_servers` (pointed at by
absolute path, so it works regardless of your working directory) —
`action_agent` has something real to call out of the box, no setup needed.

State is persisted to `mcp_servers/tickets_data.json` (not just kept in
memory), which matters because MCP's stdio transport can spawn a fresh
server subprocess per tool call depending on the client — an in-memory
dict would silently lose data between calls in that case.

**Try it directly, without going through the API:**
```bash
python scripts/demo_action_agent.py
```
This creates a ticket, lists open tickets, updates its status, and
confirms the update — all driven by natural-language requests through
the LangGraph ReAct loop deciding which tool to call each time. You'll
see it pick `create_ticket`, then `list_tickets`, then
`update_ticket_status`, then `get_ticket` on its own.

**Or through the full API + orchestration graph:**
```bash
curl -X POST http://localhost:8000/query -H "Content-Type: application/json" \
  -d '{"query": "Create a ticket for a broken checkout button, high priority"}'
```
The intent classifier routes this to `action_agent` (it matches on
"ticket"), which loads the MCP tools and lets the ReAct agent decide
what to call.

**To add your own MCP server** (a real ticketing system, calendar, CRM, etc.),
add another entry to `mcp_servers` in `config.py`:
```python
"your_server": {
    "command": "python",
    "args": ["/absolute/path/to/your_server.py"],
    "transport": "stdio",
},
```
or, for an HTTP-based MCP server:
```python
"your_server": {
    "url": "http://localhost:8100/mcp",
    "transport": "streamable_http",
},
```

## What's real vs. what's still a stub

**Working end-to-end:**
- Full LangGraph orchestration: input guardrail → intent classification → agent dispatch → output guardrail
- Real RAG: Chroma (server or embedded) + local embeddings + `ChatAnthropic` generation
- Real MCP action-taking: `mcp_servers/ticketing_server.py` (a genuine MCP server) + LangGraph's ReAct agent, wired together and working out of the box — see `scripts/demo_action_agent.py`
- Guardrails: PII/injection detection on input; confidence/citation/scope checks on output
- Tracing: local span-per-node tracing (works standalone) + automatic LangSmith tracing (when enabled)
- FastAPI: `/query`, `/ingest`, `/feedback`, `/traces/{id}`, `/health`

**Still stubbed / needs your input:**
- `agents/router.py` `_classify_intent()` — currently keyword-based; swap for a small `ChatAnthropic` call with structured output for more robust classification
- `skills/*.py` — optional composable capabilities, not currently wired into any agent (both retrieval and summarize agents inline their own logic); useful if you want to factor out shared prompt+tool combinations later
- `tools/search_tool.py` — needs a real web search API if you want it
- PII detection is regex-based — swap in something like Presidio for production-grade detection
- `mcp_servers/ticketing_server.py` uses a JSON file for storage — swap for a real database if you need concurrent access or production durability

## Scaling notes

- **Chroma via docker-compose** is the right default once you have more than a demo's worth of data or more than one API replica; the embedded mode is for local iteration only.
- **LangGraph** makes it straightforward to add checkpointing (`MemorySaver` or a DB-backed checkpointer) for multi-turn conversations, human-in-the-loop interrupts, or subgraphs — the current graph is intentionally linear/simple, but the same `StateGraph` API scales to much more complex flows.
- **LangSmith** also supports evaluation datasets and online scoring — worth setting up once you have real traffic, to catch retrieval/answer quality regressions.

## Testing

```bash
pytest tests/
```

`tests/test_guardrails.py`, `tests/test_skills.py`, and the chunker
tests run with zero external dependencies or network access.
`tests/test_agents.py` and `tests/test_api.py` require the full
`requirements.txt` installed (they instantiate `ChatAnthropic` and the
Chroma-backed retriever, which loads the local embedding model).
