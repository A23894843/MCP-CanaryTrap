"""Transparent stdio MCP proxy that injects synthetic decoys and records access.

Run as an MCP client command, for example:
  canarytrap-stdio-proxy --decoy-tool canarytrap_decoy_admin -- python server.py
Protocol traffic stays on stdout; diagnostics are written to stderr.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import threading
from typing import Any

from .gateway_core import GatewayRecorder, decoy_kind, inject_decoys, request_operation, synthetic_response
from .security_center import policy_decision


def _json_line(line: str) -> Any | None:
    try:
        return json.loads(line)
    except (json.JSONDecodeError, TypeError):
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Monitor an approved MCP stdio server through CanaryTrap")
    parser.add_argument("--connection-id", default="stdio-local")
    parser.add_argument("--decoy-tool", action="append", default=[])
    parser.add_argument("--decoy-resource", action="append", default=[])
    parser.add_argument("--decoy-prompt", action="append", default=[])
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Approved downstream server command after --")
    args = parser.parse_args()
    command = args.command[1:] if args.command and args.command[0] == "--" else args.command
    if not command:
        print("CanaryTrap: provide an approved server command after --", file=sys.stderr)
        return 2
    config = {"decoy_tools": args.decoy_tool, "decoy_resources": args.decoy_resource, "decoy_prompts": args.decoy_prompt}
    if not any(config.values()):
        print("CanaryTrap: configure at least one --decoy-tool, --decoy-resource, or --decoy-prompt", file=sys.stderr)
        return 2
    try:
        child = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=None, bufsize=0)
    except OSError as exc:
        print(f"CanaryTrap: could not start approved MCP server: {exc}", file=sys.stderr)
        return 127

    recorder = GatewayRecorder(args.connection_id, tenant=os.getenv("CANARYTRAP_DEFAULT_TENANT", "default"))
    write_lock = threading.Lock()
    state_lock = threading.Lock()
    request_methods: dict[str, str] = {}

    def emit(message: Any) -> None:
        data = json.dumps(message, separators=(",", ":"), ensure_ascii=False).encode("utf-8") + b"\n"
        with write_lock:
            sys.stdout.buffer.write(data)
            sys.stdout.buffer.flush()

    def to_child(message: Any, raw_line: str) -> None:
        if not isinstance(message, dict):
            if child.stdin:
                child.stdin.write(raw_line.encode("utf-8"))
                child.stdin.flush()
            return
        method = message.get("method")
        msg_id = message.get("id")
        operation = request_operation(message)
        if operation:
            op, target, kind = operation
            is_decoy = decoy_kind(target, config, kind) == kind
            decision = policy_decision(op, target, kind, os.getenv("CANARYTRAP_DEFAULT_TENANT", "default"))
            recorder.record(op, target[:250], kind, is_decoy, f"stdio MCP request observed; policy={decision['action']}; arguments omitted", policy_action=decision["action"])
            if decision["action"] == "deny":
                if message.get("id") is not None:
                    emit({"jsonrpc":"2.0","id":message.get("id"),"error":{"code":-32001,"message":"Blocked by MCP-CanaryTrap policy","data":{"rule_id":decision.get("rule_id"),"rule_name":decision.get("rule_name")}}})
                return
            if is_decoy:
                response = synthetic_response(message, kind, target)
                if response is not None:
                    emit(response)
                return
        if method and msg_id is not None:
            with state_lock:
                request_methods[str(msg_id)] = method
        if child.stdin:
            child.stdin.write(raw_line.encode("utf-8"))
            child.stdin.flush()

    def client_to_server() -> None:
        try:
            for line in sys.stdin.buffer:
                raw = line.decode("utf-8", errors="replace")
                message = _json_line(raw)
                to_child(message, raw)
        except (BrokenPipeError, OSError, ValueError) as exc:
            print(f"CanaryTrap stdio input stopped: {exc}", file=sys.stderr)
        finally:
            try:
                if child.stdin:
                    child.stdin.close()
            except OSError:
                pass

    def server_to_client() -> None:
        try:
            assert child.stdout is not None
            for line in iter(child.stdout.readline, b""):
                raw = line.decode("utf-8", errors="replace")
                message = _json_line(raw)
                if isinstance(message, dict) and "id" in message:
                    with state_lock:
                        method = request_methods.pop(str(message["id"]), None)
                    if method:
                        message["_canarytrap_method"] = method
                    message = inject_decoys(message, config)
                    if message is not None:
                        emit(message)
                else:
                    with write_lock:
                        sys.stdout.buffer.write(line)
                        sys.stdout.buffer.flush()
        except (BrokenPipeError, OSError) as exc:
            print(f"CanaryTrap stdio output stopped: {exc}", file=sys.stderr)

    upstream = threading.Thread(target=server_to_client, name="canarytrap-server-reader", daemon=True)
    downstream = threading.Thread(target=client_to_server, name="canarytrap-client-reader", daemon=True)
    upstream.start()
    downstream.start()
    try:
        downstream.join()
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            child.terminate()
            try:
                child.wait(timeout=2)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
    except KeyboardInterrupt:
        child.terminate()
        try:
            child.wait(timeout=2)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()
    upstream.join(timeout=2)
    return child.returncode or 0


if __name__ == "__main__":
    raise SystemExit(main())
