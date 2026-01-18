import asyncio

from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client
from mcp.client.stdio import StdioServerParameters

async def main():
    server = StdioServerParameters(
        command="python3",
        args=["mcp-wrap.py"],
        env=None,   # you can pass {"PAAS_BASE_URL": "..."} here later if needed
    )

    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("TOOLS:", [t.name for t in tools.tools])

            pkgs = await session.call_tool("paas_list_packages", {})
            print("paas_list_packages:", pkgs)

            solve = await session.call_tool(
                "paas_solve",
                {
                    "planner": "lama-first",
                    "domain": "(define (domain demo) (:predicates (p)) (:action a :precondition () :effect (p)))",
                    "problem": "(define (problem demo1) (:domain demo) (:init) (:goal (p)))",
                    "timeout_s": 30,
                    "poll_interval_s": 0.5,
                    "include_stdout": False,
                },
            )
            print("paas_solve:", solve)

asyncio.run(main())
