# MCP-CanaryTrap v1.3.2 — UI Refresh Verification

## Changes

- Replaced technical-first navigation labels with plain-language labels while retaining the existing page IDs and functionality.
- Added a first-time welcome panel and an explanation of CLEAN and FLAGGED results on the Home page.
- Refreshed the dashboard with a high-contrast light theme, clearer spacing, more legible controls, focus states, mobile layout support, and reduced-motion support.
- Rewrote key page introductions and test instructions in plain English.
- Added a glossary for decoy, flagged, clean, gateway, MCP server, and activity record.
- Clarified that gateway monitoring applies only to traffic routed through configured supported adapters.
- Updated sign-in/setup screen styling to match the dashboard.
- Changed the default application mode to protected production mode so first launch shows administrator setup; unauthenticated development mode remains an explicit `APP_ENV=development` opt-in. Tests set their environment explicitly.
- Updated package version to 1.3.2 and refreshed README navigation and scope guidance.

## Verification

- `python -m compileall -q src tests`: passed.
- `python -m pytest -q`: **42 passed, 1 skipped**.
- Dashboard inline JavaScript syntax (`node --check`): passed.

The skipped test is an existing optional integration test. The project remains a research prototype; the redesign does not expand the underlying monitoring coverage.
