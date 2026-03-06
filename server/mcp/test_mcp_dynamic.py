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

            demo_domain = """(define (domain demo)
            (:requirements :strips)
            (:predicates (p))
            (:action a
                :parameters ()
                :precondition (and)
                :effect (p)
            )
            )"""

            demo_problem = """(define (problem demo1)
            (:domain demo)
            (:init)
            (:goal (p))
            )"""

            demo_plan = "(a)"

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
                    "domain": demo_domain,
                    "problem": demo_problem,
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


            # PDDL tool tests
            print("\n--- PDDL tool syntax check tests ---")

            # Check that tool exists
            if "paas_pddl_validate_plan" not in tool_names:
                raise RuntimeError("Expected tool paas_pddl_validate_plan not found")
            
            print("\nNEGATIVE TEST: missing plan should fail")
            bad_val = await session.call_tool(
                "paas_pddl_validate_plan",
                {"domain": demo_domain, "problem": demo_problem},  # missing plan
            )
            if getattr(bad_val, "isError", False):
                print("Expected failure (isError=True)")
                print("Message:", bad_val.content[0].text if bad_val.content else "(no message)")
            else:
                print("Unexpected success (isError=False)")
                print(bad_val)

            print("\nPOSITIVE TEST: Check valid PDDL syntax of demo domain, problem, and plan")
            valid_pddl_resp = await session.call_tool(
                "paas_pddl_validate_plan",
                {"domain": demo_domain, "problem": demo_problem, "plan": demo_plan}, # borrowed from previous test
            )

            print("\nResponse from PDDL validate (valid syntax)")
            print_tool_json(valid_pddl_resp)

            print("\nPOSITIVE TEST: Check invalid PDDL syntax of demo domain, problem, and plan")
            invalid_demo_problem = """(define (problem demo1)
            (:domain demo
            (:init)
            (:goal (p))
            )""" # missing closing parenthesis for domain definition

            invalid_pddl_resp = await session.call_tool(
                "paas_pddl_validate_plan",
                {"domain": demo_domain, "problem": invalid_demo_problem, "plan": demo_plan}, # borrowed from previous test
            )

            print("\nResponse from PDDL validate (invalid syntax)")
            print_tool_json(invalid_pddl_resp)


            # Raw responses
            # print("\nRaw lama-first response:", lama_first_resp)
            # print("\nRaw VAL response:", val_resp)
            # print("\nRaw PDDL validate response (valid syntax):", valid_pddl_resp)
            # print("\nRaw PDDL validate response (invalid syntax):", invalid_pddl_resp)

asyncio.run(main())
