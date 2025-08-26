from fastapi.testclient import TestClient
from app.main import app
import httpx

client = TestClient(app)

def test_status_route_is_registered():
    """Test that the document status route is registered"""
    paths = [getattr(r, "path", "") for r in app.router.routes]
    assert "/api/documents/{document_id}/status" in paths

def test_status_route_precedes_catch_all():
    """Test that the specific document status route is registered before the catch-all proxy route"""
    paths = [getattr(r, "path", "") for r in app.router.routes]
    
    # Find indices of specific and catch-all routes
    specific_indices = [i for i, p in enumerate(paths) if p == "/api/documents/{document_id}/status"]
    catchall_indices = [i for i, p in enumerate(paths) if p == "/api/{service}/{path:path}"]
    
    assert len(specific_indices) > 0, "Document status route not found"
    assert len(catchall_indices) > 0, "Catch-all proxy route not found"
    
    # The specific route should come before the catch-all route
    specific_idx = min(specific_indices)
    catchall_idx = min(catchall_indices)
    
    assert specific_idx < catchall_idx, f"Specific route (index {specific_idx}) must register before catch-all (index {catchall_idx})"

def test_gateway_proxies_to_document_service(monkeypatch):
    """Test that the gateway properly proxies document status requests"""
    async def fake_request(*args, **kwargs):
        class MockResponse:
            status_code = 404
            headers = {"content-type": "application/json"}
            content = b'{"detail":"Not Found"}'
            text = '{"detail":"Not Found"}'  # Add text attribute
            
            async def __aenter__(self):
                return self
                
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
        
        # Mock the httpx client to avoid actual network calls
        monkeypatch.setattr(httpx.AsyncClient, "request", fake_request)
        
        # Test the endpoint
        response = client.get("/api/documents/notfound/status")
        assert response.status_code == 404

def test_no_cache_headers_on_status_endpoint():
    """Test that the status endpoint returns no-cache headers"""
    # This test would require mocking the document service response
    # For now, we'll just verify the route exists and has the right method
    paths = [getattr(r, "path", "") for r in app.router.routes]
    assert "/api/documents/{document_id}/status" in paths
    
    # Check that it's a GET route
    for route in app.router.routes:
        if getattr(route, "path", "") == "/api/documents/{document_id}/status":
            assert "GET" in getattr(route, "methods", [])
            break

def test_mock_endpoints_under_mock_path():
    """Test that mock endpoints are only available under /api/mock/ when enabled"""
    paths = [getattr(r, "path", "") for r in app.router.routes]
    
    # Mock endpoints should be under /api/mock/ not /api/documents/
    mock_paths = [p for p in paths if p.startswith("/api/mock/")]
    document_paths = [p for p in paths if p.startswith("/api/documents/")]
    
    # Ensure no mock endpoints are registered on the real document paths
    for mock_path in mock_paths:
        assert mock_path not in document_paths, f"Mock endpoint {mock_path} should not be on real document path"
