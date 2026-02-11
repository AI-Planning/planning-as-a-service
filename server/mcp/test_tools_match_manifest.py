import json, urllib.request, inspect
import mcp_wrap

base="http://localhost:5001"
pkgs=json.load(urllib.request.urlopen(base+"/package"))

fail=[]
for pkg, info in pkgs.items():
    services = info.get("endpoint", {}).get("services", {})
    for svc, man in services.items():
        tool = f"paas_{pkg}_{svc}".replace("-", "_").replace(".", "_")
        if not hasattr(mcp_wrap, tool):
            fail.append((pkg, svc, "missing tool"))
            continue
        fn = getattr(mcp_wrap, tool)
        sig = inspect.signature(fn)
        tool_params = [p for p in sig.parameters.keys() if p not in ("timeout_s","poll_interval_s")]
        manifest_params = [a["name"] for a in man.get("args", []) if "name" in a]
        if tool_params != manifest_params:
            fail.append((pkg, svc, f"mismatch tool={tool_params} manifest={manifest_params}"))

if fail:
    print("FAIL:")
    for item in fail:
        print(" -", item)
    raise SystemExit(1)
print("PASS: all tool signatures match manifest args.")
