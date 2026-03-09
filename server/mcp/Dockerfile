FROM paas:latest

COPY . /mcp
WORKDIR /mcp

ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8000
ENV MCP_TRANSPORT=streamable-http
ENV PAAS_HOST=web
ENV PAAS_PORT=5001

EXPOSE 8000

CMD ["python3", "mcp_wrap.py"]
