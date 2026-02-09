import os
import time
from typing import Any, Dict, Optional, List

import httpx
from mcp.server.fastmcp import FastMCP

# MCP server
mcp = FastMCP("PaaS-wrap")

# Config (from env)
# PAAS_BASE_URL = os.getenv("PAAS_BASE_URL", "http://localhost:5001").rstrip("/")
# DEFAULT_TIMEOUT_S = float(os.getenv("DEFAULT_TIMEOUT_S", "30"))
# DEFAULT_POLL_INTERVAL_S = float(os.getenv("DEFAULT_POLL_INTERVAL_S", "0.5"))
# HTTP_TIMEOUT_S = float(os.getenv("HTTP_TIMEOUT_S", "10"))

PAAS_BASE_URL = f"http://localhost:{os.getenv('PAAS_PORT', 5001)}" # default API destination
DEFAULT_TIMEOUT_S = int(os.getenv("TIME_LIMIT", 30)) # max time wrapper will wait for plan
DEFAULT_POLL_INTERVAL_S = float(os.getenv("MCP_POLL_INTERVAL", 0.5)) # how often we check the planner


# API helper functions
def _complete_check_url(job_tag: str) -> str:
    """
    Adds base url to the job tag returned by PaaS
    job tag format: /check/...
    output format: http://localhost:5001/check/...
    """
    if job_tag.startswith(PAAS_BASE_URL):
        return job_tag
    return PAAS_BASE_URL + job_tag

def _http_client() -> httpx.Client:
    """
    Create client to make requests to PaaS
    """
    return httpx.Client(timeout=DEFAULT_TIMEOUT_S)


# Core PaaS helper - generic API submit-and-poll function
def _submit_and_poll(
    package: str,
    service: str,
    payload: Dict[str, Any],
    timeout_s: float = DEFAULT_TIMEOUT_S,
    poll_interval_s: float = DEFAULT_POLL_INTERVAL_S,
) -> Dict[str, Any]:
    
    """
    Submit a job to a PaaS package/service and poll until completion.

    Returns:
      {
        "status": "ok" | "timeout" | "error",
        "package": "...",
        "service": "...",
        "result": "/check/...",    # from submit response
        "raw": {...},              # /check JSON on success
        "stderr": "...",           # if available
        "stdout": "...",           # if available
        "output": {...},           # if available
      }
    """

    submit_url = f"{PAAS_BASE_URL}/package/{package}/{service}"

    last_json: Optional[Dict[str, Any]] = None
    check_url: Optional[str] = None

    try:
        with _http_client() as client:
            # Submit
            r = client.post(submit_url, json=payload)
            r.raise_for_status()
            submit_json = r.json()

            # Extract check URL
            if "result" not in submit_json:
                return {
                    "status": "error",
                    "package": package,
                    "service": service,
                    "submit_url": submit_url,
                    "error": "Unexpected submit response (missing 'result')",
                    "raw_submit": submit_json,
                }

            check_url = _complete_check_url(str(submit_json["result"]))

            # Poll
            deadline = time.time() + float(timeout_s)
            while time.time() < deadline:
                cr = client.get(check_url)
                cr.raise_for_status()
                last_json = cr.json()

                if last_json.get("status") == "ok":
                    result = last_json.get("result", {}) or {}
                    return {
                        "status": "ok",
                        "package": package,
                        "service": service,
                        "check_url": check_url,
                        "output": result.get("output", {}),
                        "stdout": result.get("stdout", ""),
                        "stderr": result.get("stderr", ""),
                        "raw": last_json,
                    }

                time.sleep(float(poll_interval_s))

            return {
                "status": "timeout",
                "package": package,
                "service": service,
                "check_url": check_url,
                "timeout_s": timeout_s,
                "last": last_json,
            }

    except httpx.HTTPError as e:
        return {
            "status": "error",
            "package": package,
            "service": service,
            "submit_url": submit_url,
            "check_url": check_url,
            "error": str(e),
            "last": last_json,
        }
    except Exception as e:
        return {
            "status": "error",
            "package": package,
            "service": service,
            "submit_url": submit_url,
            "check_url": check_url,
            "error": f"Unexpected error: {type(e).__name__}: {e}",
            "last": last_json,
        }
    

# MCP tools
@mcp.tool()
def paas_list_packages() -> Dict[str, Any]:
    """
    Return installed packages and their service manifests, as provided by PaaS.
    This mirrors GET {PAAS_BASE_URL}/package.
    """
    url = f"{PAAS_BASE_URL}/package"
    try:
        with _http_client() as client:
            r = client.get(url)
            r.raise_for_status()
            return r.json()
    except httpx.HTTPError as e:
        return {"status": "error", "error": str(e), "url": url}

def _make_tool_name(package: str, service: str) -> str:
    """
    Help function to create MCP tool name from package and service names.
    E.g., package="lama", service="solve" -> "paas_lama_solve"
    """
    return f"paas_{package}_{service}".replace("-", "_").replace(".", "_")

def _register_paas_tool(
    package: str,
    service: str,
    args: List[Dict[str, Any]],
    svc_manifest: Dict[str, Any],
) -> None:
    """
    Create and register one MCP tool for package/service.

    The tool's parameters match the manifest 'args' (names), plus:
      - timeout_s
      - poll_interval_s

    We generate a function with exec() so it has an explicit signature that MCP can introspect.
    """

    tool_name = _make_tool_name(package, service)

    # Build a readable docstring for MCP based on the manifest
    arg_lines = []
    for arg in args:
        name = arg.get("name", "<missing>")
        typ = arg.get("type", "")
        desc = arg.get("description", "")
        arg_lines.append(f"- {name}: {desc} (type={typ})")
    args_block = "\n".join(arg_lines) if arg_lines else "No arguments documented."
    
    returns = svc_manifest.get("return", {}) or {}
    returns_type = returns.get("type", "<missing>")
    returns_files = returns.get("files", "<missing>")

    docstring = (
        f"{package}.{service}\n\n"
        f"Calls PaaS service `{service}` for package `{package}`.\n"
        f"POST {PAAS_BASE_URL}/package/{package}/{service}\n\n"
        f"Arguments (from manifest):\n{args_block}\n\n"
        f"Returns (from manifest):\n"
        f"- type: {returns_type}\n"
        f"- files: {returns_files}\n\n"
        f"Wrapper controls:\n"
        f"- timeout_s: max time to wait for completion (default {DEFAULT_TIMEOUT_S})\n"
        f"- poll_interval_s: seconds between polls (default {DEFAULT_POLL_INTERVAL_S})\n"
    )

    # Extract arg names for the function signature
    arg_names = [a["name"] for a in args if isinstance(a, dict) and "name" in a]

    # Build function signature based on explicit manifest args
    params = ", ".join(
        [*arg_names, "timeout_s=DEFAULT_TIMEOUT_S", "poll_interval_s=DEFAULT_POLL_INTERVAL_S"]
    )

    payload_items = ", ".join([f"'{n}': {n}" for n in arg_names])

    # Generate the function source
    src = f"""
def {tool_name}({params}):
    \"\"\"{docstring}\"\"\"
    payload = {{{payload_items}}}
    return _submit_and_poll("{package}", "{service}", payload, timeout_s=timeout_s, poll_interval_s=poll_interval_s)
"""

    # Create function in an isolated scope using Exec
    scope: Dict[str, Any] = {
        "_submit_and_poll": _submit_and_poll,
        "DEFAULT_TIMEOUT_S": DEFAULT_TIMEOUT_S,
        "DEFAULT_POLL_INTERVAL_S": DEFAULT_POLL_INTERVAL_S,
    }

    exec(src, scope)
    fn = scope[tool_name]

    globals()[tool_name] = fn

    # Register the function as an MCP tool
    mcp.tool(name=tool_name)(fn)
    print("Registered tool:", tool_name)

def _build_tools_from_manifest() -> None:
    """
    Enumerate installed packages/services from PaaS and register MCP tools for them.
    If PaaS isn't reachable at startup, we still run with only paas_list_packages().
    """

    packages = paas_list_packages()
    
    # Don't run if there is an error
    if isinstance(packages, dict) and packages.get("status") == "error":
        print(f"Error fetching packages from PaaS: {packages.get('error')}")
        return

    # Don't run if there is no response from paas_list_packages()
    if not isinstance(packages, dict):
        print("No valid response from PaaS when listing packages.")
        return

    for package_name, package_info in packages.items():
        # skip if no info
        if not isinstance(package_info, dict):
            continue

        services = (package_info.get("endpoint", {}) or {}).get("services", {}) or {}

        # only continue with this package if sure services are listed
        if not isinstance(services, dict):
            continue

        for service_name, svc_manifest in services.items():
            # ensure manifest is dict and has args
            if not isinstance(svc_manifest, dict):
                continue

            args = svc_manifest.get("args", []) or []

            # check for args list
            if not isinstance(args, list):
                args = []

            _register_paas_tool(package_name, service_name, args, svc_manifest)


# Build MCP tools at startup
_build_tools_from_manifest()
print("Dynamic tools registered.")

if __name__ == "__main__":
    mcp.run()
