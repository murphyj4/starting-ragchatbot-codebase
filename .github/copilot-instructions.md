## Quick orientation — what this project is

This is a small Retrieval-Augmented-Generation (RAG) demo: a FastAPI backend that ingests course documents from `./docs`, chunks them, stores embeddings in ChromaDB, and answers queries using Anthropic Claude. The frontend is a minimal SPA in `./frontend` (see `index.html` and `script.js`).

## High-level architecture (read these files together)
- `backend/app.py` — FastAPI entrypoint; mounts the frontend and exposes `/api/query` and `/api/courses`.
- `backend/rag_system.py` — orchestrator that wires together processing, vector store, AI, sessions, and tools.
- `backend/document_processor.py` — parses course files, detects `Lesson N:` markers, and creates text chunks (CHUNK_SIZE/CHUNK_OVERLAP in `backend/config.py`).
- `backend/vector_store.py` — ChromaDB usage: two collections `course_catalog` (metadata) and `course_content` (chunks). IDs for content use `{course_title.replace(' ', '_')}_{chunk_index}`.
- `backend/ai_generator.py` — Anthropic (Claude) client. Supports Anthropic tool calls and the ToolManager pattern.
- `backend/search_tools.py` — Tool interface + `CourseSearchTool` (tool name: `search_course_content`) and `ToolManager` used by the generator.

Read `backend/rag_system.py` + `backend/ai_generator.py` together to understand the query flow: user query -> (optional) tool search via `ToolManager` -> Claude generates final answer -> `SessionManager` stores exchanges.

## Project-specific conventions and important details
- Documents: expected in `./docs`. `DocumentProcessor.process_course_document()` looks for a first-line title (or `Course Title:`), optional `Course Link:` and `Course Instructor:` and `Lesson N:` sections. If no lessons are found the remaining text is chunked as a single document.
- Chunking: sentence-aware splitting with overlap. Defaults in `backend/config.py`: `CHUNK_SIZE=800`, `CHUNK_OVERLAP=100`.
- Vector store: uses `chromadb.PersistentClient` with `SentenceTransformer` embeddings (model set in `config.py`, default `all-MiniLM-L6-v2`). Metadata stores `lessons_json` as a serialized JSON string.
- Tools: new tools must implement the abstract `Tool` class in `backend/search_tools.py` and be registered with `ToolManager()` in `backend/rag_system.py` (see how `CourseSearchTool` is registered).
- AI rules: `AIGenerator.SYSTEM_PROMPT` encodes strict behavior (e.g., "one search per query maximum", never reveal search internals). Follow that when changing response behavior.

## Key files to edit for common tasks
- Add/change ingestion logic: `backend/document_processor.py`
- Change vector schema or embedding model: `backend/vector_store.py` and `backend/config.py`
- Add a search tool: `backend/search_tools.py` + register it in `backend/rag_system.py`
- Modify Claude prompt / tool-handling: `backend/ai_generator.py`

## How to run locally (verified from code and pyproject)
1. Create a `.env` in the project root containing at least `ANTHROPIC_API_KEY` (refer to `backend/config.py`).
2. Install dependencies (uses `pyproject.toml`): this project targets Python >= 3.13. Typical install:

```bash
python -m pip install -r <your requirements file>  # or use pipx/venv then `pip install .` if you prefer
```

3. Run the API (from repo root):

```bash
cd backend
uvicorn app:app --reload --port 8000
```

Notes: the repository had a `CLAUDE.md` with extra dev steps; there is no `run.sh` or `.env.example` in the repo — create `.env` yourself.

## API surface (important endpoints)
- POST `/api/query` — body: `{ "query": "...", "session_id": "optional" }`. Returns `{answer, sources, session_id}` (see `backend/app.py` and `backend/models.py`).
- GET `/api/courses` — returns a short stats object with total courses and titles.

## Debugging and common pitfalls
- If documents don't appear after startup, check `backend/app.py` startup block which tries to load `../docs` relative to `backend`.
- Chroma DB persistence path is `CHROMA_PATH` in `backend/config.py` (default `./chroma_db` from the backend working dir). If you move the server working dir, the path will change.
- If embeddings or Chroma calls error, check installed versions in `pyproject.toml` (Chromadb + sentence-transformers). The code uses `chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction`.
- Anthropic errors: ensure `ANTHROPIC_API_KEY` in env and the `anthropic` package version compatible with the API usage in `backend/ai_generator.py`.

## Small examples (how code is called)
- Registering a tool: see `rag_system.__init__` where `CourseSearchTool(self.vector_store)` is created and `self.tool_manager.register_tool(self.search_tool)` is called.
- Course chunk IDs: formed as `f"{course_title.replace(' ', '_')}_{chunk_index}"` in `backend/vector_store.py`.

## What to preserve when editing
- Keep the `Tool` / `ToolManager` pattern if you want to retain Anthropic tool-call flow.
- Keep course titles as the Chroma collection ID (changing that requires updating `get_existing_course_titles()`, `_resolve_course_name()` and other helpers).

If anything here is unclear, tell me which area you want expanded (examples, run/debug steps, or a summary for a new contributor) and I will iterate.
