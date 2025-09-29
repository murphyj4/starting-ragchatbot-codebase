"""
API endpoint tests for the Course Materials RAG System

These tests verify that the FastAPI endpoints handle requests and responses correctly,
including proper validation, error handling, and integration with the RAG system.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestQueryEndpoint:
    """Tests for the /api/query endpoint"""

    async def test_query_with_session_id(self, test_client: AsyncClient, mock_rag_system):
        """Test querying with an existing session ID"""
        request_data = {
            "query": "What is Python?",
            "session_id": "existing-session-123"
        }

        response = await test_client.post("/api/query", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "answer" in data
        assert "sources" in data
        assert "session_id" in data

        # Verify response content
        assert data["session_id"] == "existing-session-123"
        assert isinstance(data["answer"], str)
        assert isinstance(data["sources"], list)
        assert len(data["sources"]) > 0

        # Verify RAG system was called correctly
        mock_rag_system.query.assert_called_once_with(
            "What is Python?",
            "existing-session-123"
        )

    async def test_query_without_session_id(self, test_client: AsyncClient, mock_rag_system):
        """Test querying without a session ID (should create new session)"""
        request_data = {
            "query": "Explain machine learning"
        }

        response = await test_client.post("/api/query", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # Verify session was created
        assert data["session_id"] == "test-session-123"
        mock_rag_system.session_manager.create_session.assert_called_once()

        # Verify RAG system was called with the new session
        mock_rag_system.query.assert_called_once_with(
            "Explain machine learning",
            "test-session-123"
        )

    async def test_query_with_empty_query(self, test_client: AsyncClient):
        """Test querying with an empty query string"""
        request_data = {
            "query": ""
        }

        response = await test_client.post("/api/query", json=request_data)

        # Should still process (validation happens at RAG level if needed)
        assert response.status_code == 200

    async def test_query_missing_required_field(self, test_client: AsyncClient):
        """Test querying without the required 'query' field"""
        request_data = {
            "session_id": "test-session"
        }

        response = await test_client.post("/api/query", json=request_data)

        # Should return validation error
        assert response.status_code == 422

    async def test_query_with_invalid_json(self, test_client: AsyncClient):
        """Test querying with invalid JSON"""
        response = await test_client.post(
            "/api/query",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    async def test_query_error_handling(self, test_client: AsyncClient, mock_rag_system):
        """Test error handling when RAG system raises an exception"""
        # Configure mock to raise an exception
        mock_rag_system.query.side_effect = Exception("Database connection failed")

        request_data = {
            "query": "Test query"
        }

        response = await test_client.post("/api/query", json=request_data)

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Database connection failed" in data["detail"]

    async def test_query_response_structure(self, test_client: AsyncClient):
        """Test that query response matches expected schema"""
        request_data = {
            "query": "What are neural networks?"
        }

        response = await test_client.post("/api/query", json=request_data)
        data = response.json()

        # Verify all required fields are present
        assert "answer" in data
        assert "sources" in data
        assert "session_id" in data

        # Verify field types
        assert isinstance(data["answer"], str)
        assert isinstance(data["sources"], list)
        assert isinstance(data["session_id"], str)

        # Verify sources are strings
        for source in data["sources"]:
            assert isinstance(source, str)


@pytest.mark.integration
class TestCoursesEndpoint:
    """Tests for the /api/courses endpoint"""

    async def test_get_course_stats_success(self, test_client: AsyncClient, mock_rag_system):
        """Test successful retrieval of course statistics"""
        response = await test_client.get("/api/courses")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "total_courses" in data
        assert "course_titles" in data

        # Verify response content
        assert data["total_courses"] == 2
        assert isinstance(data["course_titles"], list)
        assert len(data["course_titles"]) == 2
        assert "Introduction to Python" in data["course_titles"]
        assert "Advanced Machine Learning" in data["course_titles"]

        # Verify RAG system was called
        mock_rag_system.get_course_analytics.assert_called_once()

    async def test_get_course_stats_empty(self, test_client: AsyncClient, mock_rag_system):
        """Test course statistics when no courses exist"""
        # Configure mock to return empty results
        mock_rag_system.get_course_analytics.return_value = {
            "total_courses": 0,
            "course_titles": []
        }

        response = await test_client.get("/api/courses")

        assert response.status_code == 200
        data = response.json()

        assert data["total_courses"] == 0
        assert data["course_titles"] == []

    async def test_get_course_stats_error_handling(self, test_client: AsyncClient, mock_rag_system):
        """Test error handling when analytics retrieval fails"""
        # Configure mock to raise an exception
        mock_rag_system.get_course_analytics.side_effect = Exception("ChromaDB connection error")

        response = await test_client.get("/api/courses")

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "ChromaDB connection error" in data["detail"]

    async def test_get_course_stats_response_structure(self, test_client: AsyncClient):
        """Test that course stats response matches expected schema"""
        response = await test_client.get("/api/courses")
        data = response.json()

        # Verify all required fields are present
        assert "total_courses" in data
        assert "course_titles" in data

        # Verify field types
        assert isinstance(data["total_courses"], int)
        assert isinstance(data["course_titles"], list)

        # Verify course titles are strings
        for title in data["course_titles"]:
            assert isinstance(title, str)


@pytest.mark.integration
class TestAPIIntegration:
    """Integration tests for multiple API operations"""

    async def test_multiple_queries_same_session(self, test_client: AsyncClient, mock_rag_system):
        """Test multiple queries using the same session ID"""
        session_id = "persistent-session-456"

        # First query
        response1 = await test_client.post("/api/query", json={
            "query": "What is Python?",
            "session_id": session_id
        })
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["session_id"] == session_id

        # Second query with same session
        response2 = await test_client.post("/api/query", json={
            "query": "Tell me more about variables",
            "session_id": session_id
        })
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["session_id"] == session_id

        # Verify RAG system was called twice with same session
        assert mock_rag_system.query.call_count == 2

    async def test_query_and_stats_workflow(self, test_client: AsyncClient, mock_rag_system):
        """Test a typical user workflow: check courses, then query"""
        # First, get available courses
        courses_response = await test_client.get("/api/courses")
        assert courses_response.status_code == 200
        courses_data = courses_response.json()
        assert courses_data["total_courses"] > 0

        # Then, make a query about one of the courses
        query_response = await test_client.post("/api/query", json={
            "query": f"Tell me about {courses_data['course_titles'][0]}"
        })
        assert query_response.status_code == 200
        query_data = query_response.json()
        assert "answer" in query_data

    async def test_concurrent_requests(self, test_client: AsyncClient):
        """Test handling of concurrent API requests"""
        import asyncio

        # Create multiple concurrent requests
        tasks = [
            test_client.post("/api/query", json={"query": f"Query {i}"})
            for i in range(5)
        ]

        responses = await asyncio.gather(*tasks)

        # Verify all requests succeeded
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert "answer" in data
            assert "session_id" in data


@pytest.mark.integration
class TestAPIValidation:
    """Tests for request/response validation"""

    async def test_query_request_validation_extra_fields(self, test_client: AsyncClient):
        """Test that extra fields in request are ignored"""
        request_data = {
            "query": "Test query",
            "session_id": "test-123",
            "extra_field": "should be ignored"
        }

        response = await test_client.post("/api/query", json=request_data)
        # FastAPI by default ignores extra fields
        assert response.status_code == 200

    async def test_query_request_wrong_type(self, test_client: AsyncClient):
        """Test validation when field has wrong type"""
        request_data = {
            "query": 123,  # Should be string
            "session_id": "test-123"
        }

        response = await test_client.post("/api/query", json=request_data)
        # Pydantic will reject wrong type and return validation error
        assert response.status_code == 422

    async def test_content_type_validation(self, test_client: AsyncClient):
        """Test that correct content-type is required"""
        response = await test_client.post(
            "/api/query",
            content='{"query": "test"}',
            headers={"Content-Type": "text/plain"}
        )

        # FastAPI should reject non-JSON content type for JSON endpoints
        assert response.status_code in [422, 415]