# Multi-page Dashboard Guide

The browser interface is arranged as a multi-page-style dashboard. Navigation changes the active view without reloading the application, while URL hashes such as `#custom-test` let users link directly to a section.

## Pages

1. **Overview** — key counts, latest verdict, recent sessions and events, and quick actions.
2. **Custom Test Lab** — structured test case form with case details, decoy registry, observed interactions, review summary, and submission.
3. **Test Sessions** — searchable/filterable session history and a detail panel for a selected session.
4. **Events & Evidence** — searchable event records, decoy filtering, latest result JSON, and copy-evidence action.
5. **Demo Lab** — run the built-in benign and overreaching scenarios.
6. **Guide & Limitations** — suggested viva flow, verdict meanings, implemented scope, and known limitations.

## Data behavior

- The dashboard fetches session and event lists from `/api/sessions` and `/api/events`.
- Built-in demonstrations use `POST /api/demo/{scenario}`.
- Custom tests use `POST /api/custom-test`.
- Latest evidence is retained in the browser's `sessionStorage` for navigation during the current browser tab session. Session and event records are persisted by the existing SQLite store.
- Search and filters are client-side views over the records returned by the API; they do not change stored records.

## Limitations

This is a multi-view dashboard served from a single HTML template, not a set of separately deployed frontend routes. The underlying test pipeline remains a research prototype: custom cases are structured, simulated event inputs, and the interface does not automatically intercept arbitrary third-party MCP traffic. Review authentication and access controls before exposing it to an untrusted public network.
