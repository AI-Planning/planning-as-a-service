import os

# MCP/API related imports
import httpx
from mcp.server.fastmcp import FastMCP

# general imports
import time
from typing import Any, Dict, Optional


# create MCP server
mcp = FastMCP("PaaS-wrap")

# config variables (constant)
PAAS_BASE_URL = f"http://localhost:{os.getenv('PAAS_PORT', 5001)}" # default API destination
DEFAULT_TIMEOUT_S = int(os.getenv("TIME_LIMIT", 30)) # max time wrapper will wait for plan
DEFAULT_POLL_INTERVAL_S = float(os.getenv("MCP_POLL_INTERVAL", 0.5)) # how often we check the planner

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

@mcp.tool()
def paas_list_packages() -> Dict[str, Any]:
    """
    Expose list of packages available through PaaS
    """
    url = f"{PAAS_BASE_URL}/package"
    try:
        with _http_client() as client:
            r = client.get(url)
            r.raise_for_status() # throw exception if response isn't HTTP 200
            return r.json()
    except httpx.HTTPError as e:
        return {"status": "error", "error": str(e), "url": url}
    
@mcp.tool()
def paas_solve(
    planner: str,
    domain: str, 
    problem: str, 
    timeout_s: float=DEFAULT_TIMEOUT_S, 
    poll_interval_s: float=DEFAULT_POLL_INTERVAL_S, 
    include_stdout: bool=False
) -> Dict[str, Any]:

    """
    Submit a solve job to PaaS and poll until complete.

    Args:
      planner: e.g., "lama-first"
      domain: PDDL domain text
      problem: PDDL problem text
      timeout_s: max time to wait for completion while polling
      poll_interval_s: how often to poll /check/<id>
      include_stdout: if True, return large stdout logs too

    Returns:
      {
        "status": "ok" | "timeout" | "error",
        "planner": "...",
        "check_url": "...",
        "plan": "...",              # if available
        "stderr": "...",            # if available
        "stdout": "...",            # optional; can be huge
        "raw": {...}                # raw /check JSON on success
      }
    """

    # URL to POST payloads to
    submit_url = f"{PAAS_BASE_URL}/package/{planner}/solve"

    # define payload itself
    payload = {"domain": domain, "problem": problem}

    try:

        with _http_client() as client:
            # submit payload
            r = client.post(submit_url, json=payload)
            r.raise_for_status() # throw exception if response isn't HTTP 200
            submit_json = r.json()

            # extract URL
            check_url = _complete_check_url(submit_json["result"])

            # poll until planner solves
            deadline = time.time() + timeout_s
            while time.time() < deadline:
                cr = client.get(check_url)
                cr.raise_for_status() # throw exception if response isn't HTTP 200
                last_json = cr.json()

                if last_json.get("status") == "ok":
                    # navigate through JSON to find plan
                    result = last_json.get("result", {}) or {}
                    output = result.get("output", {}) or {}
                    plan = output.get("sas_plan")

                    stderr = result.get("stderr", "")
                    stdout = result.get("stdout", "")

                    # format response as clean dict/JSON
                    response: Dict[str, Any] = {
                        "status": "ok",
                        "planner": planner,
                        "check_url": check_url,
                        "plan": plan,
                        "stderr": stderr,
                        "raw": last_json
                    }
                    if include_stdout:
                        response["stdout"] = stdout

                    # return dict with plan
                    return response
                
                time.sleep(poll_interval_s)
            
            # timeout
            return {
                "status": "timeout",
                "planner": planner,
                "check_url": check_url,
                "last": last_json,
                "timeout_s": timeout_s,
            }
    except httpx.HTTPError as e:
        return {
            "status": "error",
            "planner": planner,
            "error": str(e),
            "submit_url": submit_url,
            "check_url": _complete_check_url(submit_json["result"]),
            "last": last_json,
        }
    except KeyError as e:
        return {
            "status": "error",
            "planner": planner,
            "error": f"Unexpected response format, missing key: {str(e)}",
            "submit_url": submit_url,
        }


if __name__ == "__main__":
    mcp.run()
