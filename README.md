# F1 Predictor 2026 🏎️

> Professional Monte Carlo Race Prediction System — strategy-aware probabilities, uncertainty quantification, and telemetry-grade visualizations.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.34+-red.svg)](https://streamlit.io/)

---

## Overview

F1 Predictor 2026 simulates race outcomes using Monte Carlo methods to produce:

- **Win / Top-3 / Top-10 / DNF probabilities** for every driver
- **Expected finishing position** + **uncertainty bounds** (Wilson score)
- **Safety car dynamics** and **rain sensitivity** (optional)
- **Constructor aggregation**
- **Championship simulator** (remaining races)
- **HTML report generation**

The Streamlit app runs fully offline using the **hardcoded 2026 data modules** under `src/f1_predictor/data/`.

---

## Project status

- Streamlit app entrypoint: `app.py`
- Prediction engine: `src/f1_predictor/engine/*`
- HTML report generator: `src/f1_predictor/reports/html_report.py`
- Database (optional, for accuracy tracking): `src/f1_predictor/database/*`

---

## Quick start (local)

### Requirements

- Python **3.10+**
- pip

### Install

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
```

### Run Streamlit

```bash
py -m streamlit run app.py --server.port 8501
```

Open: http://localhost:8501

### Run CLI (optional)

```bash
py main.py dashboard
py main.py predict --race monaco --sims 10000
py main.py migrate-db
```

---

## Offline behavior

The app does **not require FastF1** to run predictions because it uses the built-in season/circuit/driver data modules.

FastF1 integration (`src/f1_predictor/data/fastf1_integration.py`) and scripts under `scripts/` are for optional syncing/maintenance.

---

## Docker (containerized)

```bash
docker build -t f1-predictor:latest .
docker run -p 8501:8501 f1-predictor:latest
```

Notes:
- The image runs `python main.py migrate-db` at build time.
- Streamlit starts on port `8501`.

---

## GitHub deployment readiness

### Recommended repository settings

- Use `.gitignore` for `__pycache__/`, `.venv/`, and database artifacts.
- Add CI (GitHub Actions) to run:
  - `pytest`
  - `ruff check`
  - `ruff format --check`

### Suggested folder structure

- Keep model artifacts out of the repo unless necessary.
- Treat `data/*` and `output/` as generated/runtime artifacts.

---

## Hugging Face deployment

This project is a web app (Streamlit) and a Python library/application.

Common deployment options:

1. **Spaces (Streamlit)**
   - Build with the `requirements.txt`
   - Entrypoint: `app.py`

2. **Spaces (Docker)**
   - Use the provided `Dockerfile`

If you deploy to Spaces, set environment variables for database if you want persistence:

- `F1_DATABASE_URL` (default: `sqlite:///f1_predictor.db`)

---

## Configuration

### Database

- Environment variable: `F1_DATABASE_URL`
- Default: `sqlite:///f1_predictor.db`

### Runtime parameters

Key parameters live in:

- `src/f1_predictor/config/settings.py`

---

## Development

### Test

```bash
pytest -q
```

### Lint / format

```bash
ruff check .
ruff format .
```

---

## License

MIT

---

## Version

Project version references in code: **3.x** (see `pyproject.toml`).

