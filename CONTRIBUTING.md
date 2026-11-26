# Contributing

1. Fork the repository and create a feature branch.
2. Keep security demonstrations safe and local; do not add exploit code or expose vulnerable services.
3. Add or update manual verification checks for behavior changes.
4. Never commit `.env`, API tokens, databases containing real events, or personal data.
5. Update the documentation when changing routes, configuration, or security boundaries.

## Local checks

```bash
python scripts/verify_project.py
python -m compileall app scripts
```
