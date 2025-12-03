Reto Atinna – Conversational Agent + MCP Microservices
=====================================================

This repository contains a conversational analysis system composed of:

- A **stateful conversational agent** orchestrated with LangGraph and Gemini.
- Three **MCP microservices** exposed via FastAPI:
  - Executive conversation summarization.
  - Sentiment and emotional climate analysis.
  - Propagation / virality analysis.
- A **Parquet dataset** of real conversations that the agent uses as its data source.

The agent talks to the user in natural language, decides which MCP tool to call on each request, and then explains the results in clear, executive language.


Project structure
-----------------

Repository root:

- `agent/` – Conversational agent (multi‑MCP orchestrator).
- `mcp/` – FastAPI MCP microservices for analysis.
- `data/` – Parquet dataset with conversations.
- `notebooks/` – Notebooks for EDA and dataset validation.
- `requirements.txt` – Python dependencies.

### `agent/`

- `config.py`  
  Agent configuration:
  - `GEMINI_API_KEY`, `GEMINI_MODEL`.
  - `PARQUET_PATH` – path to the Parquet file.
  - MCP URLs:
    - `MCP_RESUMEN_URL` (default `http://localhost:8000/api/v1/analysis/resumen`)
    - `MCP_SENTIMENT_URL` (default `http://localhost:8000/api/v1/analysis/sentiment`)
    - `MCP_PROPAGATION_URL` (default `http://localhost:8000/api/v1/analysis/propagation`)

- `gemini.py`  
  Gemini client with two main responsibilities:
  - `decide_tool()` – routing prompt that decides whether to use:
    - `mcp_resumen`
    - `mcp_sentiment`
    - `mcp_propagation`
    - or no tool (`tool = null`, direct answer).
  - `explain_results()` – takes the JSON returned by the MCPs and converts it into a natural language explanation.

- `memory.py`  
  Agent state model (`AgentState`), which holds:
  - `user_query`
  - `conversation_history`
  - `last_analysis` (summary + metadata)
  - `current_thread_id`
  - `tool_decision`, `tool_used`
  - `mcp_response`, `explanation`, `final_response`

- `tools.py`  
  Pydantic schemas for MCP calls:
  - `MCPResumenRequest`, `MCPResumenResponse`
  - `MCPSentimentRequest` (optional `threadId`, `messageIds`, `items`)
  - `MCPPropagationRequest` (required `root_id`, optional `messages`)
  - `AVAILABLE_TOOLS` – tool definitions.

- `parquet_Loader.py`  
  Utilities for reading the Parquet file from the agent:
  - `load_thread_messages(thread_id)` – messages for a thread in a format compatible with summary/sentiment MCPs.
  - `load_propagation_messages(root_id)` – builds the full propagation payload for the propagation MCP.

- `router.py`  
  Domain routing layer that:
  - Calls `GeminiClient.decide_tool`.
  - Validates the decision (`tool` name, arguments structure).
  - Enriches arguments when needed (for example, filling `threadId` from context or ensuring `root_id` exists).

- `nodes.py`  
  LangGraph node implementations:
  - `decide_node` – calls the router and stores `tool_decision`.
  - `resumen_node` – loads messages from Parquet by `threadId` and calls `MCP_RESUMEN_URL`.
  - `sentiment_node` – builds/limits `items` (messages) and calls `MCP_SENTIMENT_URL`.
  - `propagation_node` – builds `messages` for the thread associated to `root_id` and calls `MCP_PROPAGATION_URL`.
  - `explain_node` – uses `explain_results` to turn JSON into text.
  - `memory_node` – saves the last analysis into memory.
  - `respond_node` – produces the final user‑facing answer.

- `graph.py`  
  Defines the LangGraph graph and flow:

  - Typed state (`GraphState`) aligned with `AgentState`.
  - Registered nodes:
    - `decide`
    - `resumen`
    - `sentiment`
    - `propagation`
    - `explain`
    - `memory`
    - `respond`
  - Conditional routing:
    - `decide` → `resumen` | `sentiment` | `propagation` | `respond`
  - Main flow:
    - `resumen/sentiment/propagation` → `explain` → `memory` → `respond` → `END`.

- `main.py`  
  CLI conversational loop:
  - Initializes configuration and Gemini client.
  - Builds the graph via `create_agent_graph`.
  - Keeps a persistent `AgentState` across turns to preserve context.
  - Reads user input and prints the agent response.


### `mcp/app/`

Single FastAPI application exposing three endpoints under `/api/v1/analysis`:

- `sentiment_router.py` – `POST /sentiment`  
  - Request: `SentimentRequest` with `items: [{id, text}, ...]`.
  - Uses `GeminiSentimentClient` to analyze each item (batching and JSON recovery).

- `resumen_router.py` – `POST /resumen`  
  - Request: `ResumenRequest` with `threadId` and `messages` (`MessageInput`).  
  - Calls `ResumenService` which:
    - Cleans and normalizes the conversation text.
    - Builds a structured analysis prompt.
    - Calls Gemini and validates the JSON response.

- `propagation_router.py` – `POST /propagation`  
  - Request: `PropagationRequest` with `root_id` and `messages` (conversation tree).  
  - `compute_propagation` computes:
    - Depth levels, reply timing, unique authors.
    - A propagation score and the top engaged replies.

The agent always talks to these services over HTTP using `httpx`; it never calls their internal Python APIs directly.


Installation
------------

Prerequisites:

- Python 3.11
- Gemini API key.

### 1. Create and activate virtual environment

```bash
python -m venv venv
venv\Scripts\activate  # Windows PowerShell
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables (`.env`)

In the project root, create a `.env` file with at least:

```env
GEMINI_API_KEY=your_api_key
GEMINI_MODEL=gemini-2.5-pro

# Path to the Parquet dataset
PARQUET_PATH=./data/Reto_data.parquet

# Optional: override MCP URLs if you change host/port
MCP_RESUMEN_URL=http://localhost:8000/api/v1/analysis/resumen
MCP_SENTIMENT_URL=http://localhost:8000/api/v1/analysis/sentiment
MCP_PROPAGATION_URL=http://localhost:8000/api/v1/analysis/propagation
```


Running the services
--------------------

### 1. Start the MCP API (FastAPI)

From the project root:

```bash
venv\Scripts\activate
uvicorn mcp.app.main:app --reload --port 8000
```

Main endpoints:

- `GET  /docs` – interactive documentation (Swagger).
- `POST /api/v1/analysis/resumen`
- `POST /api/v1/analysis/sentiment`
- `POST /api/v1/analysis/propagation`

### 2. Run the conversational agent

In another terminal (with the same venv activated):

```bash
python -m agent.main
```

You should see a prompt like:

```text
AGENTE CONVERSACIONAL

Escribe 'salir' o 'exit' para terminar.

Usuario:
```

You can interact in Spanish or English; the routing prompt and explanations are optimized for Spanish conversation analysis, but the architecture is language‑agnostic.


Recommended use cases
---------------------

### Executive summary (mcp_resumen)

Example question to the agent:

> Haz un resumen ejecutivo del thread tikapi_... ¿cuáles son los temas clave y los riesgos?

Flow:

- `decide` chooses `mcp_resumen` and fills `threadId` (from user or context).
- `resumen_node` loads the thread messages from Parquet and calls the summary MCP.
- `explain_node` converts the structured JSON into an executive‑style narrative.


### Sentiment / emotional climate (mcp_sentiment)

Example:

> ¿Cuál es el clima emocional general del thread tikapi_...?  

Flow:

- `decide` prioritizes `mcp_sentiment` because the intent is emotional.
- `sentiment_node`:
  - Resolves `threadId` from arguments or context.
  - Loads the thread from Parquet.
  - Builds `items = [{id, text}, ...]` and limits them to a configurable maximum.
  - Calls `/api/v1/analysis/sentiment`.


### Propagation / virality (mcp_propagation)

Example:

> Analiza la propagación del mensaje raíz tikapi_7520805329748151557 en este dataset. ¿Qué tan viral fue y cuáles son las respuestas más influyentes?

Flow:

- `decide` detects propagation intent → selects `mcp_propagation`.
- `propagation_node`:
  - Uses `root_id` to find the corresponding `threadId` in the Parquet dataset.
  - Builds the `messages` array in the exact shape expected by the propagation MCP.
  - Calls `/api/v1/analysis/propagation`.
  - `explain_node` returns a narrative analysis (virality level, structure of reply levels, anomalies such as bot‑like behavior, etc.).


Design notes
------------

- The agent does not call MCP internals; it always uses the HTTP API, just like any external client would.
- Agent memory (`last_analysis`, `current_thread_id`, conversation history) allows multi‑turn workflows:
  - First, summarize a thread.
  - Then, ask follow‑up questions about emotional climate or propagation without repeating IDs.
- The Parquet dataset is only read from the agent side to build rich payloads for MCPs; the MCP services themselves are agnostic to where the data comes from.



