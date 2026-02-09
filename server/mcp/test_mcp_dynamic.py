import asyncio
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

async def main():
    server = StdioServerParameters(
        command="python3",
        args=["mcp_wrap.py"],
        env=None,
    )

    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            tool_names = [t.name for t in tools.tools]
            print("TOOLS:", tool_names[:20], "... total:", len(tool_names))

            # Check that your dynamic lama-first tool exists
            if "paas_lama_first_solve" not in tool_names:
                raise RuntimeError("Expected tool paas_lama_first_solve not found")

            # Positive and negative test cases for the dynamic tool
            print("\nNEGATIVE TEST: wrong arg name domainX should fail")
            bad = await session.call_tool(
                "paas_lama_first_solve",
                {"domainX": "...", "problem": "..."},
            )
            if getattr(bad, "isError", False):
                print("Expected failure (isError=True)")
                print("Message:", bad.content[0].text if bad.content else "(no message)")
            else:
                print("Unexpected success (isError=False)")
                print(bad)

            # Call it
            resp = await session.call_tool(
                "paas_lama_first_solve",
                {
                    "domain": "(define (domain demo) (:predicates (p)) (:action a :precondition () :effect (p)))",
                    "problem": "(define (problem demo1) (:domain demo) (:init) (:goal (p)))",
                    "timeout_s": 30,
                    "poll_interval_s": 0.5,
                },
            )
            print("Raw response:", resp)

asyncio.run(main())
