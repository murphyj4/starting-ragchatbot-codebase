"""
Shared pytest fixtures for testing the Course Materials RAG System
"""

import sys
import os
from pathlib import Path
from typing import List
from unittest.mock import Mock, MagicMock

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from httpx import AsyncClient, ASGITransport
from pydantic import BaseModel

# Add backend directory to path for imports
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from config import Config
from models import Course, Lesson, CourseChunk


# Request/Response models (copied from app.py to avoid static files import issue)
class QueryRequest(BaseModel):
    """Request model for course queries"""
    query: str
    session_id: str | None = None


class QueryResponse(BaseModel):
    """Response model for course queries"""
    answer: str
    sources: List[str]
    session_id: str


class CourseStats(BaseModel):
    """Response model for course statistics"""
    total_courses: int
    course_titles: List[str]


@pytest.fixture
def mock_config():
    """Provides a mock configuration for testing"""
    return Config(
        ANTHROPIC_API_KEY="test-api-key",
        ANTHROPIC_MODEL="claude-sonnet-4-20250514",
        EMBEDDING_MODEL="all-MiniLM-L6-v2",
        CHUNK_SIZE=800,
        CHUNK_OVERLAP=100,
        MAX_RESULTS=5,
        MAX_HISTORY=2,
        CHROMA_PATH="./test_chroma_db"
    )


@pytest.fixture
def sample_courses():
    """Provides sample course data for testing"""
    return [
        Course(
            title="Introduction to Python",
            instructor="John Doe",
            course_link="https://example.com/python",
            lessons=[
                Lesson(lesson_number=1, title="Getting Started", lesson_link="https://example.com/python/1"),
                Lesson(lesson_number=2, title="Variables and Types", lesson_link="https://example.com/python/2"),
            ]
        ),
        Course(
            title="Advanced Machine Learning",
            instructor="Jane Smith",
            course_link="https://example.com/ml",
            lessons=[
                Lesson(lesson_number=1, title="Neural Networks", lesson_link="https://example.com/ml/1"),
                Lesson(lesson_number=2, title="Deep Learning", lesson_link="https://example.com/ml/2"),
            ]
        )
    ]


@pytest.fixture
def sample_chunks(sample_courses):
    """Provides sample course chunks for testing"""
    chunks = []
    for course in sample_courses:
        for i, lesson in enumerate(course.lessons):
            chunks.append(CourseChunk(
                content=f"Content for {course.title} - {lesson.title}",
                course_title=course.title,
                lesson_number=lesson.lesson_number,
                chunk_index=i
            ))
    return chunks


@pytest.fixture
def mock_rag_system(sample_courses):
    """Provides a mocked RAG system for testing"""
    rag_system = Mock()

    # Mock session manager
    rag_system.session_manager = Mock()
    rag_system.session_manager.create_session.return_value = "test-session-123"

    # Mock query method
    rag_system.query.return_value = (
        "This is a test answer from the RAG system.",
        ["Source 1: Introduction to Python - Getting Started", "Source 2: Advanced Machine Learning - Neural Networks"]
    )

    # Mock analytics method
    rag_system.get_course_analytics.return_value = {
        "total_courses": len(sample_courses),
        "course_titles": [course.title for course in sample_courses]
    }

    # Mock add_course_folder method
    rag_system.add_course_folder.return_value = (len(sample_courses), 10)

    return rag_system


@pytest.fixture
def test_app(mock_rag_system):
    """
    Creates a test FastAPI app without static file mounting.
    This avoids import issues with the frontend directory in tests.
    """
    app = FastAPI(title="Course Materials RAG System - Test", root_path="")

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Define API endpoints inline (same as app.py but without static files)
    @app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest):
        """Process a query and return response with sources"""
        try:
            # Create session if not provided
            session_id = request.session_id
            if not session_id:
                session_id = mock_rag_system.session_manager.create_session()

            # Process query using RAG system
            answer, sources = mock_rag_system.query(request.query, session_id)

            return QueryResponse(
                answer=answer,
                sources=sources,
                session_id=session_id
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats():
        """Get course analytics and statistics"""
        try:
            analytics = mock_rag_system.get_course_analytics()
            return CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"]
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return app


@pytest.fixture
async def test_client(test_app):
    """
    Provides an async HTTP client for testing API endpoints
    """
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_anthropic_client():
    """Provides a mocked Anthropic client for testing"""
    client = Mock()

    # Mock the messages.create method
    mock_response = Mock()
    mock_response.content = [Mock(text="This is a mocked AI response.")]
    mock_response.stop_reason = "end_turn"

    client.messages.create.return_value = mock_response

    return client


@pytest.fixture
def mock_vector_store():
    """Provides a mocked vector store for testing"""
    store = Mock()

    # Mock search methods
    store.search_metadata.return_value = [
        {"course_title": "Introduction to Python", "lesson_title": "Getting Started"}
    ]
    store.search_content.return_value = [
        {"content": "Sample content", "course_title": "Introduction to Python"}
    ]

    # Mock add methods
    store.add_course_metadata.return_value = None
    store.add_course_chunks.return_value = None

    return store