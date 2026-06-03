# Config Directory

This directory stores human-editable YAML configuration files for major system components.

Goals:

- Keep runtime and prompt configuration separate from Python code
- Make model and RAG tuning easier during iteration
- Support future environment-specific overrides

Suggested usage:

- Keep `core/config.py` for environment variables and infrastructure paths
- Keep this directory for business-level component settings
- Load these YAML files through a dedicated config loader in a later step

Current files:

- `agent.yaml`
- `chroma.yaml`
- `ingestion.yaml`
- `model.yaml`
- `prompt.yaml`
- `rag.yaml`
