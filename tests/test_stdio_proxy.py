# Annotated source file for MCP-CanaryTrap v1.3.2.
# Lines beginning with "Explanation:" describe the following statement or branch.
# Original executable statements are preserved; comments are for learning.

# Explanation: Imports modules that this file uses.
import json
# Explanation: Imports modules that this file uses.
import os
# Explanation: Imports modules that this file uses.
import subprocess
# Explanation: Imports modules that this file uses.
import sys
# Explanation: Imports names from pathlib.
from pathlib import Path


# Explanation: Function test_stdio_proxy_injects_decoy_and_intercepts_access: implements the operation described by its name and body.
def test_stdio_proxy_injects_decoy_and_intercepts_access(tmp_path):
    # Explanation: Assigns or updates a value used later by this function or module.
    server = tmp_path / "mock_server.py"
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    server.write_text('''import json, sys\nfor line in sys.stdin:\n m=json.loads(line)\n if m.get("method")=="tools/list":\n  print(json.dumps({"jsonrpc":"2.0","id":m["id"],"result":{"tools":[{"name":"safe_tool","inputSchema":{"type":"object"}}]}}),flush=True)\n elif m.get("method")=="tools/call":\n  print(json.dumps({"jsonrpc":"2.0","id":m["id"],"result":{"content":[{"type":"text","text":"upstream called"}]}}),flush=True)\n''')
    # Explanation: Assigns or updates a value used later by this function or module.
    env = os.environ.copy()
    # Explanation: Assigns or updates a value used later by this function or module.
    env["PYTHONPATH"] = str(Path(__file__).parents[1] / "src")
    # Explanation: Assigns or updates a value used later by this function or module.
    env["CANARYTRAP_DB"] = str(tmp_path / "events.sqlite3")
    # Explanation: Assigns or updates a value used later by this function or module.
    requests = [
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "ct_decoy", "arguments": {}}},
    ]
    # Explanation: Assigns or updates a value used later by this function or module.
    result = subprocess.run(
        [sys.executable, "-m", "mcp_canarytrap.stdio_proxy", "--connection-id", "test", "--decoy-tool", "ct_decoy", "--", sys.executable, str(server)],
        input="\n".join(json.dumps(x) for x in requests) + "\n",
        text=True, capture_output=True, timeout=10, env=env, cwd=Path(__file__).parents[1],
    )
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert result.returncode == 0, result.stderr
    # Explanation: Assigns or updates a value used later by this function or module.
    responses = {item["id"]: item for item in map(json.loads, result.stdout.splitlines())}
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert {tool["name"] for tool in responses[1]["result"]["tools"]} == {"safe_tool", "ct_decoy"}
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert "ct_decoy" in responses[2]["result"]["content"][0]["text"]
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert "upstream called" not in responses[2]["result"]["content"][0]["text"]


# Explanation: Function test_stdio_proxy_enforces_deny_policy: implements the operation described by its name and body.
def test_stdio_proxy_enforces_deny_policy(tmp_path):
    # Explanation: Imports names from fastapi.testclient.
    from fastapi.testclient import TestClient
    # Explanation: Imports names from mcp_canarytrap.
    from mcp_canarytrap import api
    # Explanation: Assigns or updates a value used later by this function or module.
    db_path=tmp_path/"policy-stdio.sqlite3"
    # Explanation: Assigns or updates a value used later by this function or module.
    env=os.environ.copy()
    # Explanation: Assigns or updates a value used later by this function or module.
    env["PYTHONPATH"]=str(Path(__file__).parents[1]/"src")
    # Explanation: Assigns or updates a value used later by this function or module.
    env["CANARYTRAP_DB"]=str(db_path)
    # Explanation: Assigns or updates a value used later by this function or module.
    env["CANARYTRAP_RBAC_KEYS"]=""
    # Explanation: Assigns or updates a value used later by this function or module.
    old_db=os.environ.get("CANARYTRAP_DB")
    # Explanation: Assigns or updates a value used later by this function or module.
    os.environ["CANARYTRAP_DB"]=str(db_path)
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Explanation: Assigns or updates a value used later by this function or module.
        client=TestClient(api.app)
        # Explanation: Assigns or updates a value used later by this function or module.
        rule=client.post("/api/security/policies",json={"name":"Block export","operation":"tools/call","target_pattern":"sensitive_export","action":"deny"})
        # Explanation: Assert an expected condition; a false condition raises AssertionError.
        assert rule.status_code==200
    finally:
        # Explanation: Conditional decision: execute the following branch only when this expression is true.
        # Explanation: Branches based on this condition; the indented block runs only when it evaluates to true.
        if old_db is None: os.environ.pop("CANARYTRAP_DB",None)
        # Explanation: Fallback branch used when the preceding condition(s) were not satisfied.
        else: os.environ["CANARYTRAP_DB"]=old_db
    # Explanation: Assigns or updates a value used later by this function or module.
    server=tmp_path/"mock_server.py"
    # Explanation: Assigns or updates a value used later by this function or module.
    server.write_text("import json, sys\nfor line in sys.stdin:\n m=json.loads(line)\n print(json.dumps({'jsonrpc':'2.0','id':m.get('id'),'result':{'content':[{'type':'text','text':'upstream called'}]}}),flush=True)\n")
    # Explanation: Assigns or updates a value used later by this function or module.
    requests=[{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"sensitive_export","arguments":{}}}]
    # Explanation: Assigns or updates a value used later by this function or module.
    result=subprocess.run([sys.executable,"-m","mcp_canarytrap.stdio_proxy","--connection-id","test-policy","--decoy-tool","ct_decoy","--",sys.executable,str(server)],
      input="\n".join(json.dumps(x) for x in requests)+"\n",text=True,capture_output=True,timeout=10,env=env,cwd=Path(__file__).parents[1])
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert result.returncode==0,result.stderr
    # Explanation: Assigns or updates a value used later by this function or module.
    payload=json.loads(result.stdout.strip().splitlines()[0])
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert payload["error"]["code"]==-32001
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert "upstream called" not in result.stdout
