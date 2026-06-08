# F1 Predictor 2026 🏎️

> Professional Monte Carlo Race Prediction System — powered by **FastF1 live data** with strategy-aware probabilities, uncertainty quantification, and telemetry-grade visualizations.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.34+-red.svg)](https://streamlit.io/)
[![FastF1](https://img.shields.io/badge/FastF1-v3.8+-orange.svg)](https://docs.fastf1.dev/)

---

## Overview

F1 Predictor 2026 simulates race outcomes using Monte Carlo methods to produce:

- **Win / Top-3 / Top-5 / Top-10 / DNF probabilities** for every driver
- **Expected finishing position** + **uncertainty bounds** (Wilson score)
- **Safety car dynamics** and **rain sensitivity**
- **Constructor aggregation**
- **Championship simulator** (remaining races)
- **HTML report generation**
- **Accuracy audit** with Brier Score tracking

### v5.0 — FastF1 Live Data Integration

All prediction features are now **grounded in real F1 data** via the [FastF1](https://docs.fastf1.dev/) library:

| Feature | Data Source | Fallback |
|---|---|---|
| Constructor strength | Actual team pace rankings from race data | Hardcoded ratings |
| Driver wet skill | Measured wet-vs-dry pace delta | Subjective 1–10 rating |
| Track fit | Historical circuit-specific lap pace | Static track_type_fit labels |
| Recent form | Pace delta to field median + finishing positions | Finishing positions only |
| DNF probability | Circuit-specific DNF rates from race history | Career averages |
| Safety car upside | Actual SC frequency per circuit | Static probability |
| Tyre degradation | Linear regression slopes per compound per circuit | Estimated curves |
| Weather model | Historical rainfall/track temp from session data | Static defaults |
| ELO ratings | Updated from real race finishing orders | Manual entry |

**Every function uses a "live data first, static fallback" pattern** — the system never breaks if FastF1 is unavailable.

---

## Project Structure

```
├── app.py                          # Streamlit UI entrypoint
├── main.py                         # CLI entrypoint (Click)
├── requirements.txt
├── src/
│   ├── api/                        # FastAPI routes & schemas
│   ├── config/                     # Settings, feature weights
│   ├── data/                       # Data layer
│   │   ├── fastf1_integration.py   # ★ FastF1 pipeline (8 analysis functions)
│   │   ├── driver_data.py          # Driver database + FastF1 refresh
│   │   ├── circuit_data.py         # Circuit database + FastF1 refresh
│   │   ├── season_2026.py          # Season results & standings
│   │   └── teams.py                # Team normalization
│   ├── engine/                     # Prediction engine (pure computation)
│   │   ├── predictor.py            # Orchestrator + live data flag
│   │   ├── feature_engineering.py  # Feature pipeline + FastF1 cache
│   │   ├── probability_model.py    # Monte Carlo simulation
│   │   ├── multi_dimensional_elo.py# ELO system + FastF1 ingestion
│   │   ├── tire_strategy.py        # Tyre model + FastF1 degradation
│   │   ├── weather_model_v3.py     # Weather + FastF1 historical data
│   │   └── cache.py                # Thread-safe prediction cache
│   ├── database/                   # SQLAlchemy ORM + SQLite
│   └── reports/                    # HTML report generator
├── f1_cache/                       # FastF1 persistent cache (auto-created)
└── output/                         # Generated reports
```

---

## Quick Start

### Requirements

- Python **3.10+**
- pip

### Install

```bash
py -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
```

### Run Streamlit

```bash
py -m streamlit run app.py --server.port 8501
```

Open: http://localhost:8501

### Run CLI

```bash
py main.py dashboard
py main.py predict --race monaco --sims 10000
py main.py predict --race canada --sims 20000 --rain 0.35 --seed 42 --store
py main.py report --race canada --sims 10000 --rain 0.2
py main.py migrate-db
```

---

## FastF1 Integration

### How It Works

The system uses a **layered data architecture**:

```
FastF1 API  →  src/data/fastf1_integration.py  →  src/engine/feature_engineering.py  →  Predictions
                     (data ingestion)                    (feature cache + compute)
```

1. **Data Ingestion** (`src/data/fastf1_integration.py`): 8 advanced analysis functions pull real data from FastF1
2. **Feature Cache** (`src/engine/feature_engineering.py`): `refresh_fastf1_cache()` pre-loads data at startup
3. **Prediction Pipeline**: Every `compute_*` function tries FastF1 data first, falls back to static values

### Available Analysis Functions

| Function | Purpose |
|---|---|
| `get_driver_pace_metrics(season, race)` | Avg pace, consistency, sector splits per driver |
| `get_tyre_degradation_curves(season, race)` | Linear regression slope per compound per driver |
| `get_circuit_historical_stats(circuit, seasons)` | DNF rate, SC frequency, rainfall across years |
| `get_wet_weather_performance(seasons)` | Wet-vs-dry pace delta → objective wet skill rating |
| `get_qualifying_vs_race_pace(season, race)` | Racer-vs-qualifier rating |
| `get_constructor_pace_rankings(season)` | Team pace from actual race data |
| `refresh_driver_database(season)` | Pull latest results/standings |
| `get_circuit_telemetry_profile(circuit, seasons)` | Top speed, speed index per circuit |

### ELO Integration

| Function | Purpose |
|---|---|
| `ingest_fastf1_results(season, race)` | Update ELO from a single race result |
| `ingest_season_elo(season)` | Sequentially update ELO for all races in a season |

### Data Refresh

```python
# Refresh all FastF1 data at app startup
from src.engine.feature_engineering import refresh_fastf1_cache
refresh_fastf1_cache(season=2025)

# Refresh driver database from FastF1
from src.data.driver_data import refresh_from_fastf1
refresh_from_fastf1(season=2025)

# Refresh circuit stats from FastF1
from src.data.circuit_data import refresh_circuits_from_fastf1
refresh_circuits_from_fastf1(seasons=[2025, 2024, 2023])

# Use live data in predictions
from src.engine.predictor import PredictionRequest, predict
request = PredictionRequest(circuit_id="canada", use_live_data=True)
result = predict(request)
# result["meta"]["data_source"] → "fastf1_live"
# result["meta"]["data_freshness"] → "2025-06-08T..."
```

### Offline Mode

The app runs **fully offline** without FastF1. All features gracefully fall back to static/hardcoded data:

- Constructor strength → built-in ratings dict
- Driver stats → manually maintained `src/data/driver_data.py`
- Circuit properties → built-in `src/data/circuit_data.py`
- Weather → static defaults

FastF1 is installed via `requirements.txt` but is **optional at runtime**.

---

## Configuration

### Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `F1_DATABASE_URL` | `sqlite:///f1_predictor.db` | Database connection string |
| `WEATHER_API_KEY` | *(none)* | OpenWeatherMap API for live forecasts |

### Key Config Files

- `src/config/settings.py` — Feature weights, simulation parameters, ELO K-factors
- `src/data/driver_data.py` — Driver database (auto-refreshable from FastF1)
- `src/data/circuit_data.py` — Circuit database (auto-refreshable from FastF1)
- `src/data/season_2026.py` — Current season results and standings

---

## Docker

```bash
docker build -t f1-predictor:latest .
docker run -p 8501:8501 f1-predictor:latest
```

Notes:
- The image runs `py main.py migrate-db` at build time.
- Streamlit starts on port `8501`.
- FastF1 cache is persisted in the container's `f1_cache/` directory.

---

## Deployment

### Hugging Face Spaces (Streamlit)

- Build with `requirements.txt`
- Entrypoint: `app.py`
- Set `F1_DATABASE_URL` for database persistence

### Hugging Face Spaces (Docker)

- Use the provided `Dockerfile`

---

## Development

### Test

```bash
py -m pytest -q
```

### Lint / Format

```bash
ruff check .
ruff format .
```

---

## Tech Stack

| Component | Technology |
|---|---|
| Frontend | Streamlit ≥1.34 |
| Backend | Python 3.11, Click CLI, Rich |
| Data | Pandas ≥2.0, NumPy ≥1.24, **FastF1 ≥3.1** |
| ML/Modelling | Scikit-learn, Optuna (hyperparameter tuning) |
| Database | SQLAlchemy ≥2.0 + SQLite |
| Visualisation | Plotly (interactive charts), Rich (terminal tables) |
| Config | Pydantic ≥2.0 |
| Testing | Pytest ≥7.4 |

---

## License

MIT

---

## Version

**5.0** — FastF1 Live Data Integration