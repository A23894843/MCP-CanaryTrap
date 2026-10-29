# Annotated source file for MCP-CanaryTrap v1.3.2.
# Lines beginning with "Explanation:" describe the following statement or branch.
# Original executable statements are preserved; comments are for learning.

# Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
"""Transparent stdio MCP proxy that injects synthetic decoys and records access.

Run as an MCP client command, for example:
  canarytrap-stdio-proxy --decoy-tool canarytrap_decoy_admin -- python server.py
Protocol traffic stays on stdout; diagnostics are written to stderr.
"""
# Explanation: Imports names from __future__.
from __future__ import annotations

# Explanation: Imports modules that this file uses.
import argparse
# Explanation: Imports modules that this file uses.
import json
# Explanation: Imports modules that this file uses.
import os
# Explanation: Imports modules that this file uses.
import subprocess
# Explanation: Imports modules that this file uses.
import sys
# Explanation: Imports modules that this file uses.
import threading
# Explanation: Imports names from typing.
from typing import Any

# Explanation: Imports names from gateway_core.
from .gateway_core import GatewayRecorder, decoy_kind, inject_decoys, request_operation, synthetic_response
# Explanation: Imports names from security_center.
from .security_center import policy_decision


# Explanation: Function _json_line: implements the operation described by its name and body.
def _json_line(line: str) -> Any | None:
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Explanation: Return this result to the caller; this ends the current function path.
        return json.loads(line)
    except (json.JSONDecodeError, TypeError):
        # Explanation: Return this result to the caller; this ends the current function path.
        return None


# Explanation: Function main: implements the operation described by its name and body.
def main() -> int:
    # Explanation: Assigns or updates a value used later by this function or module.
    parser = argparse.ArgumentParser(description="Monitor an approved MCP stdio server through CanaryTrap")
    # Explanation: Assigns or updates a value used later by this function or module.
    parser.add_argument("--connection-id", default="stdio-local")
    # Explanation: Assigns or updates a value used later by this function or module.
    parser.add_argument("--decoy-tool", action="append", default=[])
    # Explanation: Assigns or updates a value used later by this function or module.
    parser.add_argument("--decoy-resource", action="append", default=[])
    # Explanation: Assigns or updates a value used later by this function or module.
    parser.add_argument("--decoy-prompt", action="append", default=[])
    # Explanation: Assigns or updates a value used later by this function or module.
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Approved downstream server command after --")
    # Explanation: Assigns or updates a value used later by this function or module.
    args = parser.parse_args()
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    command = args.command[1:] if args.command and args.command[0] == "--" else args.command
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if not command:
        # Explanation: Assigns or updates a value used later by this function or module.
        print("CanaryTrap: provide an approved server command after --", file=sys.stderr)
        # Explanation: Return this result to the caller; this ends the current function path.
        return 2
    # Explanation: Assigns or updates a value used later by this function or module.
    config = {"decoy_tools": args.decoy_tool, "decoy_resources": args.decoy_resource, "decoy_prompts": args.decoy_prompt}
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if not any(config.values()):
        # Explanation: Assigns or updates a value used later by this function or module.
        print("CanaryTrap: configure at least one --decoy-tool, --decoy-resource, or --decoy-prompt", file=sys.stderr)
        # Explanation: Return this result to the caller; this ends the current function path.
        return 2
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Explanation: Assigns or updates a value used later by this function or module.
        child = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=None, bufsize=0)
    except OSError as exc:
        # Explanation: Assigns or updates a value used later by this function or module.
        print(f"CanaryTrap: could not start approved MCP server: {exc}", file=sys.stderr)
        # Explanation: Return this result to the caller; this ends the current function path.
        return 127

    # Explanation: Assigns or updates a value used later by this function or module.
    recorder = GatewayRecorder(args.connection_id, tenant=os.getenv("CANARYTRAP_DEFAULT_TENANT", "default"))
    # Explanation: Assigns or updates a value used later by this function or module.
    write_lock = threading.Lock()
    # Explanation: Assigns or updates a value used later by this function or module.
    state_lock = threading.Lock()
    # Explanation: Assigns or updates a value used later by this function or module.
    request_methods: dict[str, str] = {}

    # Explanation: Function emit: implements the operation described by its name and body.
    def emit(message: Any) -> None:
        # Explanation: Assigns or updates a value used later by this function or module.
        data = json.dumps(message, separators=(",", ":"), ensure_ascii=False).encode("utf-8") + b"\n"
        # Explanation: Acquire/manage the context resource and release it reliably on exit.
        with write_lock:
            # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
            sys.stdout.buffer.write(data)
            # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
            sys.stdout.buffer.flush()

    # Explanation: Function to_child: implements the operation described by its name and body.
    def to_child(message: Any, raw_line: str) -> None:
        # Explanation: Conditional decision: execute the following branch only when this expression is true.
        if not isinstance(message, dict):
            # Explanation: Conditional decision: execute the following branch only when this expression is true.
            if child.stdin:
                # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
                child.stdin.write(raw_line.encode("utf-8"))
                # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
                child.stdin.flush()
            # Explanation: Return this result to the caller; this ends the current function path.
            return
        # Explanation: Assigns or updates a value used later by this function or module.
        method = message.get("method")
        # Explanation: Assigns or updates a value used later by this function or module.
        msg_id = message.get("id")
        # Explanation: Assigns or updates a value used later by this function or module.
        operation = request_operation(message)
        # Explanation: Conditional decision: execute the following branch only when this expression is true.
        if operation:
            # Explanation: Assigns or updates a value used later by this function or module.
            op, target, kind = operation
            # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
            is_decoy = decoy_kind(target, config, kind) == kind
            # Explanation: Assigns or updates a value used later by this function or module.
            decision = policy_decision(op, target, kind, os.getenv("CANARYTRAP_DEFAULT_TENANT", "default"))
            # Explanation: Assigns or updates a value used later by this function or module.
            recorder.record(op, target[:250], kind, is_decoy, f"stdio MCP request observed; policy={decision['action']}; arguments omitted", policy_action=decision["action"])
            # Explanation: Conditional decision: execute the following branch only when this expression is true.
            if decision["action"] == "deny":
                # Explanation: Conditional decision: execute the following branch only when this expression is true.
                if message.get("id") is not None:
                    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
                    emit({"jsonrpc":"2.0","id":message.get("id"),"error":{"code":-32001,"message":"Blocked by MCP-CanaryTrap policy","data":{"rule_id":decision.get("rule_id"),"rule_name":decision.get("rule_name")}}})
                # Explanation: Return this result to the caller; this ends the current function path.
                return
            # Explanation: Conditional decision: execute the following branch only when this expression is true.
            if is_decoy:
                # Explanation: Assigns or updates a value used later by this function or module.
                response = synthetic_response(message, kind, target)
                # Explanation: Conditional decision: execute the following branch only when this expression is true.
                if response is not None:
                    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
                    emit(response)
                # Explanation: Return this result to the caller; this ends the current function path.
                return
        # Explanation: Conditional decision: execute the following branch only when this expression is true.
        if method and msg_id is not None:
            # Explanation: Acquire/manage the context resource and release it reliably on exit.
            with state_lock:
                # Explanation: Assigns or updates a value used later by this function or module.
                request_methods[str(msg_id)] = method
        # Explanation: Conditional decision: execute the following branch only when this expression is true.
        if child.stdin:
            # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
            child.stdin.write(raw_line.encode("utf-8"))
            # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
            child.stdin.flush()

    # Explanation: Function client_to_server: implements the operation described by its name and body.
    def client_to_server() -> None:
        # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
        try:
            # Explanation: Loop over each item in the iterable and run the indented body.
            for line in sys.stdin.buffer:
                # Explanation: Assigns or updates a value used later by this function or module.
                raw = line.decode("utf-8", errors="replace")
                # Explanation: Assigns or updates a value used later by this function or module.
                message = _json_line(raw)
                # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
                to_child(message, raw)
        except (BrokenPipeError, OSError, ValueError) as exc:
            # Explanation: Assigns or updates a value used later by this function or module.
            print(f"CanaryTrap stdio input stopped: {exc}", file=sys.stderr)
        finally:
            # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
            try:
                # Explanation: Conditional decision: execute the following branch only when this expression is true.
                if child.stdin:
                    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
                    child.stdin.close()
            except OSError:
                # Explanation: Intentional no-op placeholder; this block performs no action.
                pass

    # Explanation: Function server_to_client: implements the operation described by its name and body.
    def server_to_client() -> None:
        # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
        try:
            # Explanation: Assert an expected condition; a false condition raises AssertionError.
            assert child.stdout is not None
            # Explanation: Loop over each item in the iterable and run the indented body.
            for line in iter(child.stdout.readline, b""):
                # Explanation: Assigns or updates a value used later by this function or module.
                raw = line.decode("utf-8", errors="replace")
                # Explanation: Assigns or updates a value used later by this function or module.
                message = _json_line(raw)
                # Explanation: Conditional decision: execute the following branch only when this expression is true.
                if isinstance(message, dict) and "id" in message:
                    # Explanation: Acquire/manage the context resource and release it reliably on exit.
                    with state_lock:
                        # Explanation: Assigns or updates a value used later by this function or module.
                        method = request_methods.pop(str(message["id"]), None)
                    # Explanation: Conditional decision: execute the following branch only when this expression is true.
                    if method:
                        # Explanation: Assigns or updates a value used later by this function or module.
                        message["_canarytrap_method"] = method
                    # Explanation: Assigns or updates a value used later by this function or module.
                    message = inject_decoys(message, config)
                    # Explanation: Conditional decision: execute the following branch only when this expression is true.
                    if message is not None:
                        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
                        emit(message)
                else:
                    # Explanation: Acquire/manage the context resource and release it reliably on exit.
                    with write_lock:
                        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
                        sys.stdout.buffer.write(line)
                        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
                        sys.stdout.buffer.flush()
        except (BrokenPipeError, OSError) as exc:
            # Explanation: Assigns or updates a value used later by this function or module.
            print(f"CanaryTrap stdio output stopped: {exc}", file=sys.stderr)

    # Explanation: Assigns or updates a value used later by this function or module.
    upstream = threading.Thread(target=server_to_client, name="canarytrap-server-reader", daemon=True)
    # Explanation: Assigns or updates a value used later by this function or module.
    downstream = threading.Thread(target=client_to_server, name="canarytrap-client-reader", daemon=True)
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    upstream.start()
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    downstream.start()
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        downstream.join()
        # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
        try:
            # Explanation: Assigns or updates a value used later by this function or module.
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
            child.terminate()
            # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
            try:
                # Explanation: Assigns or updates a value used later by this function or module.
                child.wait(timeout=2)
            except subprocess.TimeoutExpired:
                # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
                child.kill()
                # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
                child.wait()
    except KeyboardInterrupt:
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        child.terminate()
        # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
        try:
            # Explanation: Assigns or updates a value used later by this function or module.
            child.wait(timeout=2)
        except subprocess.TimeoutExpired:
            # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
            child.kill()
            # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
            child.wait()
    # Explanation: Assigns or updates a value used later by this function or module.
    upstream.join(timeout=2)
    # Explanation: Return this result to the caller; this ends the current function path.
    return child.returncode or 0


# Explanation: Conditional decision: execute the following branch only when this expression is true.
if __name__ == "__main__":
    # Explanation: Raise an exception to reject the operation or report a failure.
    raise SystemExit(main())
