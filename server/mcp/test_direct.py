import importlib.util
import json
from pathlib import Path

# Load mcp-wrap.py even though it has a hyphen
path = Path(__file__).parent / "mcp-wrap.py"
spec = importlib.util.spec_from_file_location("mcp_wrap", path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

print("Calling paas_list_packages() ...")
pkgs = mod.paas_list_packages()
print("Type:", type(pkgs))
# print a couple keys
if isinstance(pkgs, dict):
    print("Example packages:", list(pkgs.keys())[:5])
else:
    print(pkgs)

print("\nCalling paas_solve(lama-first) ...")
res = mod.paas_solve(
    planner="lama-first",
    domain="(define (domain demo) (:predicates (p)) (:action a :precondition () :effect (p)))",
    problem="(define (problem demo1) (:domain demo) (:init) (:goal (p)))",
    timeout_s=30,
    poll_interval_s=0.5,
    include_stdout=False,
)
print(json.dumps(res, indent=4))
