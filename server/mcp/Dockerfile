FROM paas:latest

ENV MCP_HOST 0.0.0.0
ENV MCP_PORT 5002
ENV MCP_TRANSPORT streamable-http

ENV PAAS_HOST web
ENV PAAS_PORT 5001
# Change to https if the API is served over HTTPS in deployment.
ENV PAAS_SCHEME https

COPY . /mcp
WORKDIR /mcp

# expose the app port
EXPOSE 5002

# run the app server. If you need https, use the command below instead.
CMD ["python3", "mcp_wrap.py"]

# run the app server with https.
# CMD ["uvicorn", "mcp_asgi:app", "--host", "0.0.0.0", "--port", "5002", "--ssl-certfile", "/etc/letsencrypt/live/paas-uom.org/fullchain.pem", "--ssl-keyfile", "/etc/letsencrypt/live/paas-uom.org/privkey.pem"]
