import json
import os
import subprocess
import sys
from pathlib import Path


def test_stdio_proxy_injects_decoy_and_intercepts_access(tmp_path):
    server = tmp_path / "mock_server.py"
    server.write_text('''import json, sys\nfor line in sys.stdin:\n m=json.loads(line)\n if m.get("method")=="tools/list":\n  print(json.dumps({"jsonrpc":"2.0","id":m["id"],"result":{"tools":[{"name":"safe_tool","inputSchema":{"type":"object"}}]}}),flush=True)\n elif m.get("method")=="tools/call":\n  print(json.dumps({"jsonrpc":"2.0","id":m["id"],"result":{"content":[{"type":"text","text":"upstream called"}]}}),flush=True)\n''')
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parents[1] / "src")
    env["CANARYTRAP_DB"] = str(tmp_path / "events.sqlite3")
    requests = [
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "ct_decoy", "arguments": {}}},
    ]
    result = subprocess.run(
        [sys.executable, "-m", "mcp_canarytrap.stdio_proxy", "--connection-id", "test", "--decoy-tool", "ct_decoy", "--", sys.executable, str(server)],
        input="\n".join(json.dumps(x) for x in requests) + "\n",
        text=True, capture_output=True, timeout=10, env=env, cwd=Path(__file__).parents[1],
    )
    assert result.returncode == 0, result.stderr
    responses = {item["id"]: item for item in map(json.loads, result.stdout.splitlines())}
    assert {tool["name"] for tool in responses[1]["result"]["tools"]} == {"safe_tool", "ct_decoy"}
    assert "ct_decoy" in responses[2]["result"]["content"][0]["text"]
    assert "upstream called" not in responses[2]["result"]["content"][0]["text"]


def test_stdio_proxy_enforces_deny_policy(tmp_path):
    from fastapi.testclient import TestClient
    from mcp_canarytrap import api
    db_path=tmp_path/"policy-stdio.sqlite3"
    env=os.environ.copy()
    env["PYTHONPATH"]=str(Path(__file__).parents[1]/"src")
    env["CANARYTRAP_DB"]=str(db_path)
    env["CANARYTRAP_RBAC_KEYS"]=""
    old_db=os.environ.get("CANARYTRAP_DB")
    os.environ["CANARYTRAP_DB"]=str(db_path)
    try:
        client=TestClient(api.app)
        rule=client.post("/api/security/policies",json={"name":"Block export","operation":"tools/call","target_pattern":"sensitive_export","action":"deny"})
        assert rule.status_code==200
    finally:
        if old_db is None: os.environ.pop("CANARYTRAP_DB",None)
        else: os.environ["CANARYTRAP_DB"]=old_db
    server=tmp_path/"mock_server.py"
    server.write_text("import json, sys\nfor line in sys.stdin:\n m=json.loads(line)\n print(json.dumps({'jsonrpc':'2.0','id':m.get('id'),'result':{'content':[{'type':'text','text':'upstream called'}]}}),flush=True)\n")
    requests=[{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"sensitive_export","arguments":{}}}]
    result=subprocess.run([sys.executable,"-m","mcp_canarytrap.stdio_proxy","--connection-id","test-policy","--decoy-tool","ct_decoy","--",sys.executable,str(server)],
      input="\n".join(json.dumps(x) for x in requests)+"\n",text=True,capture_output=True,timeout=10,env=env,cwd=Path(__file__).parents[1])
    assert result.returncode==0,result.stderr
    payload=json.loads(result.stdout.strip().splitlines()[0])
    assert payload["error"]["code"]==-32001
    assert "upstream called" not in result.stdout
