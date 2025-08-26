# API Gateway Route Ordering Fix

## Problem Description

The `/api/documents/{document_id}/status` endpoint was returning mock/random payloads instead of properly proxying to the document service. This was caused by route ordering issues where catch-all or mock routes were intercepting requests before they reached the real handler.

## Root Cause

FastAPI matches routes in registration order - the first match wins. If a catch-all route or mock handler is registered before the specific document status route, it will intercept all requests to that path.

## Fixes Implemented

### 1. Route Table Logging on Startup

Added startup logging to show the exact order of route registration:

```python
@app.on_event("startup")
def _log_routes():
    """Log all registered routes in registration order for debugging"""
    logging.info("=== ROUTE TABLE (registration order) ===")
    for i, r in enumerate(app.router.routes):
        path = getattr(r, "path", str(r))
        methods = getattr(r, "methods", [])
        name = getattr(r, "name", "")
        logging.info("%03d: %s  methods=%s  name=%s", i, path, methods, name)
    logging.info("=== END ROUTE TABLE ===")
```

**Verification**: Check API Gateway logs for "ROUTE TABLE" entries on startup.

### 2. Specific Route Registration Order

Ensured the document status route is registered before any catch-all proxy routes:

```python
@app.get("/api/documents/{document_id}/status")
async def get_document_status(document_id: str, request: Request):
    # ... specific implementation
```

**Verification**: Route table should show this route before the catch-all proxy.

### 3. Catch-All Proxy Route (Last)

Added a catch-all proxy route at the very end to handle unmatched API calls:

```python
# MUST be last of all /api routes - catch-all proxy for any unmatched API calls
@app.api_route("/api/{service}/{path:path}",
               methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS"])
async def proxy_catch_all(service: str, path: str, request: Request):
    # ... catch-all implementation
```

**Verification**: This route should appear last in the route table.

### 4. Mock Endpoints Under Separate Path

Moved mock endpoints to `/api/mock/...` to prevent interference with real endpoints:

```python
if settings.ENABLE_GATEWAY_MOCKS:
    @app.get("/api/mock/documents/{document_id}/status")
    def _mock_document_status(document_id: str):
        # ... mock implementation
```

**Verification**: No mocks should be registered on `/api/documents/...` paths.

### 5. No-Cache Headers for Status Endpoint

Added cache control headers to prevent caching of status responses:

```python
return Response(
    content=response.content,
    media_type="application/json",
    headers={
        "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        "Pragma": "no-cache",
    }
)
```

**Verification**: Status endpoint responses should include no-cache headers.

### 6. Environment Variable Control

Added `ENABLE_GATEWAY_MOCKS` environment variable to control mock behavior:

```bash
# In .env files
ENABLE_GATEWAY_MOCKS=false
```

**Verification**: Mocks should only be active when this is set to `true`.

## Testing

### Automated Tests

Run the test suite to verify route ordering:

```bash
cd services/api-gateway
python -m pytest tests/ -v
```

### Manual Testing

Use the provided test script:

```bash
./test_route_ordering.sh
```

### Verification Steps

1. **Check Route Table**: Look for "ROUTE TABLE" in API Gateway logs
2. **Verify Order**: Ensure document status route comes before catch-all
3. **Test Endpoint**: Call `/api/documents/test-123/status` and verify 404 from document service
4. **Check Headers**: Verify no-cache headers are present
5. **Test Catch-All**: Call `/api/unknown-service/test` and verify 404 response

## Expected Behavior

### Before Fix
- Random mock responses with `{state, progress}` on `/api/documents/{id}/status`
- Debug logs never firing
- Requests intercepted by catch-all or mock routes

### After Fix
- Requests properly reach document service
- 404 responses for non-existent documents (from document service)
- No-cache headers on status responses
- Clear logging of proxy calls
- Mock endpoints only available under `/api/mock/...` when enabled

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `ENABLE_GATEWAY_MOCKS` | `false` | Enable/disable mock endpoints |

## Files Modified

- `services/api-gateway/app/main.py` - Route ordering and logging
- `services/api-gateway/app/config.py` - Mock configuration
- `services/api-gateway/tests/test_document_status_route.py` - Route ordering tests
- `env.local.example` - Environment variable documentation
- `env.cloud.example` - Cloud environment configuration

## Troubleshooting

### Route Still Not Working

1. Check route table logs: `docker logs <container> | grep "ROUTE TABLE"`
2. Verify document service is running: `docker compose ps document-service`
3. Check environment variables: `ENABLE_GATEWAY_MOCKS=false`
4. Run tests: `cd services/api-gateway && python -m pytest tests/`

### Mock Still Responding

1. Ensure `ENABLE_GATEWAY_MOCKS=false`
2. Check that mocks are only under `/api/mock/...`
3. Verify route registration order in logs

### Cache Headers Missing

1. Check if using the specific endpoint (not catch-all)
2. Verify Response object is being returned with headers
3. Check browser developer tools for response headers

## Prevention

To prevent this issue from regressing:

1. **Tests**: Run route ordering tests before deployment
2. **Code Review**: Ensure new routes are added in the correct order
3. **Logging**: Monitor route table logs on startup
4. **Documentation**: Keep this document updated with any route changes

## Related Issues

- Mock endpoints interfering with real API calls
- Route ordering problems in FastAPI applications
- Cache control for dynamic endpoints
- API gateway proxy configuration
