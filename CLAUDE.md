# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Course Materials RAG (Retrieval-Augmented Generation) System - a full-stack web application that enables users to query course materials and receive intelligent, context-aware responses. It uses ChromaDB for vector storage, Anthropic's Claude for AI generation, and provides a web interface for interaction.

## Development Commands

### Environment Setup
```bash
# Install dependencies
uv sync

# Set up environment variables (create .env with ANTHROPIC_API_KEY)
cp .env.example .env
# Then edit .env with your actual Anthropic API key
```

### Running the Application
```bash
# Quick start (recommended)
chmod +x run.sh
./run.sh

# Manual start
cd backend && uv run uvicorn app:app --reload --port 8000
```

### Development URLs
- Web Interface: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`

## Architecture Overview

### Backend Structure (`/backend`)
The backend follows a modular architecture with clear separation of concerns:

- **`app.py`**: FastAPI application entry point with CORS, static file serving, and API endpoints
- **`rag_system.py`**: Main orchestrator that coordinates all components for RAG functionality
- **`config.py`**: Centralized configuration using environment variables and dataclasses
- **`models.py`**: Pydantic models for Course, Lesson, and CourseChunk data structures
- **`vector_store.py`**: ChromaDB integration for vector storage and semantic search
- **`document_processor.py`**: Text processing, chunking, and course content extraction
- **`ai_generator.py`**: Anthropic Claude API integration for response generation
- **`session_manager.py`**: User session handling and conversation history management
- **`search_tools.py`**: Tool system for structured course search capabilities

### Frontend Structure (`/frontend`)
Simple vanilla HTML/CSS/JavaScript frontend:
- **`index.html`**: Single-page application with chat interface and course statistics
- **`script.js`**: Frontend JavaScript for API communication and UI interactions
- **`style.css`**: Complete styling for the web interface

### Key Architectural Patterns

#### RAG Pipeline Flow
1. **Document Processing**: Course documents → structured Course/Lesson models → text chunks
2. **Vector Storage**: Text chunks → embeddings → ChromaDB collections (course_metadata + course_content)
3. **Query Processing**: User query → semantic search → relevant chunks → context for Claude
4. **Response Generation**: Context + query + conversation history → Claude API → structured response

#### Data Models
- **Course**: Contains title, instructor, lessons list, and optional course link
- **Lesson**: Sequential lesson with number, title, and optional lesson link
- **CourseChunk**: Text chunk with course context, lesson number, and chunk position

#### Session Management
- Each user interaction can have an optional session_id for conversation continuity
- Session manager maintains conversation history with configurable max history length
- Sessions auto-create if not provided

## Key Configuration

### Environment Variables (`.env`)
- `ANTHROPIC_API_KEY`: Required for Claude API access
- Other settings are configured in `config.py` with sensible defaults

### ChromaDB Collections
- `course_metadata`: Stores course and lesson metadata for semantic course discovery
- `course_content`: Stores chunked course content for detailed content search

### Embedding and AI Models
- Embedding: `all-MiniLM-L6-v2` (SentenceTransformers)
- AI Model: `claude-sonnet-4-20250514` (Anthropic)
- Chunk Size: 800 characters with 100 character overlap

## Course Document Format

The system expects course documents in `/docs` directory with the following structure:
- Course title extraction from document content
- Lesson number and title parsing
- Automatic text chunking for vector storage
- Optional lesson and course link extraction

## Development Notes

### Adding New Tools
The system uses a tool manager pattern in `search_tools.py`. To add new search capabilities:
1. Create a new tool class implementing the base tool interface
2. Register it with the ToolManager in `rag_system.py`
3. The AI generator will automatically discover and use available tools

### Vector Store Operations
- Course metadata and content are stored in separate ChromaDB collections
- Semantic search operates on both collections for comprehensive results
- Vector store supports course analytics and statistics extraction

### FastAPI Integration
- Static files served from `/frontend` directory with development-friendly no-cache headers
- CORS configured for development with wildcard origins
- API endpoints follow RESTful patterns with Pydantic request/response models