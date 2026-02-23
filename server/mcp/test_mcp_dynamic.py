import asyncio
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

import json


# JSON print tool
def print_tool_json(result):
    if getattr(result, "isError", False):
        print("ERROR:", result.content[0].text if result.content else "Unknown error")
        return

    if not result.content:
        print("No content returned")
        return

    text = result.content[0].text
    try:
        parsed = json.loads(text)
        print(json.dumps(parsed, indent=2))
    except Exception:
        print(text)


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

            # ----- lama-first solve tool tests -----
            print("\n--- lama-first solve tests ---")

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
            lama_first_resp = await session.call_tool(
                "paas_lama_first_solve",
                {
                    "domain": "(define (domain demo) (:predicates (p)) (:action a :precondition () :effect (p)))",
                    "problem": "(define (problem demo1) (:domain demo) (:init) (:goal (p)))",
                    "timeout_s": 30,
                    "poll_interval_s": 0.5,
                },
            )

            # Printed lama-first response
            print("\nResponse from lama-first solve")
            print_tool_json(lama_first_resp)


            # ----- VAL validate tool tests -----
            print("\n--- VAL validate tests ---")

            # Check that tool exists
            if "paas_val_validate" not in tool_names:
                raise RuntimeError("Expected tool paas_val_validate not found")

            # define inputs
            demo_domain = "(define (domain demo) (:predicates (p)) (:action a :precondition () :effect (p)))"
            demo_problem = "(define (problem demo1) (:domain demo) (:init) (:goal (p)))"
            demo_plan = "; plan for demo\n0: (a) [1]\n"

            print("\nNEGATIVE TEST: missing plan should fail")
            bad_val = await session.call_tool(
                "paas_val_validate",
                {"domain": demo_domain, "problem": demo_problem},  # missing plan
            )
            if getattr(bad_val, "isError", False):
                print("Expected failure (isError=True)")
                print("Message:", bad_val.content[0].text if bad_val.content else "(no message)")
            else:
                print("Unexpected success (isError=False)")
                print(bad_val)

            print("\nPOSITIVE TEST: VAL validate demo plan")
            val_resp = await session.call_tool(
                "paas_val_validate",
                {"domain": demo_domain, "problem": demo_problem, "plan": demo_plan},
            )

            print("\nResponse from VAL validate")
            print_tool_json(val_resp)

            # Raw responses
            print("\nRaw lama-first response:", lama_first_resp)
            print("\nRaw VAL response:", val_resp)

asyncio.run(main())
