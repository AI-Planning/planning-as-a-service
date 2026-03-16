from mcp_wrap import mcp

# ASGI app used by uvicorn when running MCP with TLS.
app = mcp.streamable_http_app
