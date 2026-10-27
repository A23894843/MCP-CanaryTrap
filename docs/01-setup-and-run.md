# Setup and Run

## Requirements
- Python 3.11 or newer (Python 3.12 is recommended for the container build).
- Internet access for first-time dependency installation.
- Optional: Docker Engine and Docker Compose.

## Local setup (Kali Linux / Linux)
From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Use `python -m pytest`, not bare `pytest`, if your operating system's system pytest imports system packages rather than the virtual environment.

## Run tests
```bash
python -m pytest -v
```

## Run both scenarios in the terminal
```bash
python -m mcp_canarytrap.demo --scenario both --db ./reports/demo.sqlite3
```

Expected: benign scenario `CLEAN`; overreaching scenario `FLAGGED` with three decoy evidence IDs.

## Run the dashboard
```bash
python -m mcp_canarytrap.api
```
Open `http://127.0.0.1:8000` in a browser. API docs are available at `http://127.0.0.1:8000/docs`.

## Docker
```bash
docker compose up --build
```
Open `http://127.0.0.1:8000`. The compose file binds the service to localhost only.

## Database
The default SQLite file is `canarytrap.sqlite3` in the current directory. Set `CANARYTRAP_DB` to change the path. Do not commit database files or real sensitive data.
