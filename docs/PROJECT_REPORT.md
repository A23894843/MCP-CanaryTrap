# MCP-CanaryTrap — Project Report

## Abstract
MCP-CanaryTrap is an educational security monitoring prototype built around an instrumented Model Context Protocol server. It exposes a normal demonstration tool and fictional decoy tools. A deterministic rule checks tool names when invoked. Access to a configured decoy creates a SQLite event containing target, event type, severity, message, source, and timestamp. FastAPI exposes monitoring endpoints and a browser dashboard displays event summaries and history. The prototype does not use machine learning and does not claim to monitor arbitrary external MCP servers.

## Problem statement
Demonstrate a simple and explainable way to detect and record calls to selected decoy tools in an instrumented MCP server.

## Objectives
1. Implement an MCP server with normal and decoy tools.
2. Detect exact configured decoy names.
3. Assign policy-based severity.
4. Store events in SQLite.
5. Expose event data through FastAPI.
6. Display summaries and event history in a dashboard.
7. Demonstrate the system using a Python MCP client and manual verification.

## Methodology
A tool wrapper calls the detector when invoked. The detector compares the tool name against configured decoys. On a match, the server stores an event in SQLite. The FastAPI dashboard retrieves statistics and event history.

## Technology
Python, MCP Python SDK, FastAPI, Uvicorn, SQLite, HTML, CSS, JavaScript.

## Manual verification
Run FastAPI, open the dashboard, run the MCP client, call `weather_search`, and verify no decoy event. Then call each decoy and verify corresponding event records and severity. Capture screenshots from the actual machine. Do not claim results that were not personally verified.

## Limitations
Detection covers only calls through this instrumented server and uses exact-name matching. It does not establish intent, inspect arbitrary third-party MCP servers, or monitor all network traffic. Authentication, remote alert delivery, and tamper-resistant logging are not included.

## Conclusion
The prototype demonstrates the end-to-end flow of tool invocation, deterministic decoy detection, event storage, API retrieval, and dashboard presentation.
