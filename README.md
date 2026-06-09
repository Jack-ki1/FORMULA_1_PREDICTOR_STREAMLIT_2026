# Formula 1 Predictor Streamlit 2026

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.34+-red.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Version](https://img.shields.io/badge/Version-5.0-orange.svg)

**Advanced F1 Race Prediction System with Monte Carlo Simulation & Machine Learning**

[Features](#features) • [Installation](#installation) • [Quick Start](#quick-start) • [Architecture](#architecture) • [API Reference](#api-reference) • [Contributing](#contributing)

</div>

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [System Requirements](#system-requirements)
- [Installation Guide](#installation-guide)
  - [Prerequisites](#prerequisites)
  - [Local Installation](#local-installation)
  - [Docker Deployment](#docker-deployment)
  - [Hugging Face Spaces](#hugging-face-spaces)
- [Quick Start](#quick-start)
  - [Web Interface (Streamlit)](#web-interface-streamlit)
  - [REST API](#rest-api)
- [Architecture](#architecture)
  - [System Design](#system-design)
  - [Layer Separation](#layer-separation)
  - [Data Flow](#data-flow)
  - [Module Structure](#module-structure)
- [Core Components](#core-components)
  - [Prediction Engine](#prediction-engine)
  - [Feature Engineering](#feature-engineering)
  - [Monte Carlo Simulation](#monte-carlo-simulation)
  - [Calibration System](#calibration-system)
  - [Weather Modeling](#weather-modeling)
  - [Tire Strategy](#tire-strategy)
  - [ELO Rating System](#elo-rating-system)
- [Data Sources](#data-sources)
  - [Static Data](#static-data)
  - [Dynamic Data Integration](#dynamic-data-integration)
  - [FastF1 Integration](#fastf1-integration)
  - [Ergast API](#ergast-api)
- [Configuration](#configuration)
  - [Environment Variables](#environment-variables)
  - [Feature Weights](#feature-weights)
  - [Simulation Parameters](#simulation-parameters)
- [Usage Examples](#usage-examples)
  - [Basic Race Prediction](#basic-race-prediction)
  - [Head-to-Head Comparison](#head-to-head-comparison)
  - [Championship Forecast](#championship-forecast)
  - [Constructor Analysis](#constructor-analysis)
  - [HTML Report Generation](#html-report-generation)
  - [Backtesting](#backtesting)
- [Prediction Methodology](#prediction-methodology)
  - [Probability Model](#probability-model)
  - [Multi-Dimensional ELO](#multi-dimensional-elo)
  - [Vectorized Simulation](#vectorized-simulation)
  - [Confidence Intervals](#confidence-intervals)
  - [DNF Risk Assessment](#dnf-risk-assessment)
- [Performance Optimization](#performance-optimization)
  - [Caching Strategy](#caching-strategy)
  - [Parallel Processing](#parallel-processing)
  - **Memory Management](#memory-management)
- [Testing](#testing)
  - [Unit Tests](#unit-tests)
  - [Integration Tests](#integration-tests)
  - [Invariant Testing](#invariant-testing)
- [Database Schema](#database-schema)
  - [Tables Overview](#tables-overview)
  - [Migration Guide](#migration-guide)
- **API Documentation](#api-documentation)
  - [Endpoints](#endpoints)
  - [Request/Response Schemas](#requestresponse-schemas)
  - [Authentication](#authentication)
- [Deployment](#deployment)
  - [Production Setup](#production-setup)
  - [Nginx Configuration](#nginx-configuration)
  - [Monitoring](#monitoring)
- **Troubleshooting](#troubleshooting)
  - [Common Issues](#common-issues)
  - [Debug Mode](#debug-mode)
  - [Log Analysis](#log-analysis)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

---

## Overview

Formula 1 Predictor Streamlit 2026 is a state-of-the-art race prediction system designed specifically for the 2026 F1 season. It combines advanced statistical modeling, machine learning techniques, and real-time data integration to provide accurate probabilistic forecasts for Grand Prix outcomes.

### What Makes This System Unique?

1. **Probabilistic Approach**: Unlike deterministic predictions, our system provides probability distributions for all possible outcomes, enabling better risk assessment and decision-making.

2. **Multi-Factor Analysis**: Integrates 8+ feature dimensions including driver ELO ratings, constructor strength, recent form, track type compatibility, reliability metrics, weather conditions, safety car probabilities, and grid positions.

3. **Monte Carlo Simulation**: Performs thousands of race simulations using vectorized NumPy operations, completing 50,000 simulations in under 1 second on modern hardware.

4. **Real-Time Adaptation**: Dynamically adjusts predictions based on live qualifying results, weather updates, and tire strategy choices.

5. **Calibration Tracking**: Maintains prediction accuracy through continuous calibration against historical results, automatically detecting when model parameters need updating.

6. **Professional Reporting**: Generates publication-quality HTML reports with interactive charts, suitable for team analysis, media coverage, or fan engagement.

7. **Flexible Integration**: REST API enables programmatic access for automation, custom dashboards, and third-party integrations.

### Use Cases

- **Team Strategy Planning**: Evaluate different tire strategies and pit stop windows
- **Broadcasting & Media**: Provide data-driven insights during race coverage
- **Betting & Fantasy Sports**: Make informed decisions based on probability distributions
- **Fan Engagement**: Interactive predictions and head-to-head comparisons
- **Academic Research**: Study patterns in motorsport performance and uncertainty quantification

---

## Key Features

### 🏁 Race Prediction
- Full race result probability distributions
- Win, podium, points finish probabilities
- DNF (Did Not Finish) risk assessment
- Expected finishing position with confidence intervals
- Value betting identification (over/under-priced drivers)

### 👥 Head-to-Head Analysis
- Direct driver vs driver win probability
- Qualifying battle predictions
- Teammate performance comparison
- Historical matchup statistics

### 🏆 Championship Forecasting
- Season-long championship simulation
- Remaining race scenario analysis
- Points trajectory projections
- Constructor championship predictions

### 🌦️ Weather Impact Modeling
- Rain probability integration
- Track condition effects on performance
- Tire degradation adjustments
- Safety car probability calculations

### 🛞 Tire Strategy Simulation
- Compound selection impact
- Pit stop timing optimization
- Degradation rate modeling
- Undercut/overcut analysis

### 📊 Advanced Analytics
- Driver radar charts (pace, consistency, wet weather, overtaking, reliability)
- Constructor strength trends
- Circuit characteristic analysis
- Performance decomposition

### 📈 Accuracy Tracking
- Brier Score calculation
- Log loss evaluation
- Calibration plots
- Historical prediction audit trail

### 🎨 Professional Reports
- Customizable HTML report generation
- Interactive Plotly charts
- Exportable PDF format
- Shareable static files

### 🔧 Flexible Configuration
- Adjustable feature weights
- Tunable simulation parameters
- Custom circuit databases
- Driver trait overrides

---

## System Requirements

### Minimum Requirements
- **Operating System**: Windows 10/11, macOS 10.15+, Linux (Ubuntu 20.04+)
- **Python**: 3.11 or higher
- **RAM**: 4 GB
- **Storage**: 500 MB free space
- **Internet**: Required for FastF1 data fetching

### Recommended Requirements
- **Python**: 3.12
- **RAM**: 8 GB or higher (for large-scale simulations)
- **CPU**: Multi-core processor (for parallel simulations)
- **Storage**: 2 GB free space (for database and cache)
- **GPU**: Optional (for accelerated ML inference)

### Supported Python Versions
- ✅ Python 3.11
- ✅ Python 3.12
- ⚠️ Python 3.10 (limited support, some features may not work)
- ❌ Python 3.9 and below (not supported)

### Browser Compatibility (Web Interface)
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

---

## Installation Guide

### Prerequisites

Before installing, ensure you have:

1. **Python 3.11+ installed**
   ```bash
   # Check Python version
   python --version
   # or
   py --version  # Windows
   ```

2. **pip package manager**
   ```bash
   # Check pip version
   pip --version
   ```

3. **Git (optional, for cloning repository)**
   ```bash
   git --version
   ```

### Local Installation

#### Step 1: Clone or Download Project

```bash
# If you have Git
git clone <repository-url>
cd FORMULA_1_PREDICTOR_STREAMLIT_2026

# Or download ZIP and extract
```

#### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

The `requirements.txt` includes:
```
streamlit>=1.34.0
pandas>=2.0.0
numpy>=1.24.0
fastf1>=3.1.0
pydantic>=2.0.0
sqlalchemy>=2.0.0
click>=8.1.0
rich>=13.0.0
plotly>=5.18.0
optuna>=3.4.0
scikit-learn>=1.3.0
pytest>=7.4.0
requests>=2.31.0
python-dotenv>=1.0.0
```

#### Step 4: Initialize Database

```python
# Using Python directly
from src.database.models import init_db
init_db()
```

This creates `f1_predictor.db` SQLite database with all required tables.

#### Step 5: Verify Installation

```bash
# Run tests
pytest tests/ -v

# Check module imports
python -c "from src.engine.predictor import predict; print('✓ All imports successful')"
```

### Docker Deployment

#### Option 1: Build from Source

```bash
# Build Docker image
docker build -t f1-predictor:latest .

# Run container
docker run -d \
  --name f1-predictor \
  -p 8501:8501 \
  -v $(pwd)/data:/app/data \
  -e F1_DATABASE_URL=sqlite:///./data/f1_predictor.db \
  f1-predictor:latest
```

#### Option 2: Use Pre-built Image

```bash
# Pull from registry (when available)
docker pull f1predictor/streamlit:latest

# Run
docker run -d -p 8501:8501 f1predictor/streamlit:latest
```

#### Docker Compose (Recommended for Production)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8501:8501"
    environment:
      - F1_DATABASE_URL=sqlite:///./data/f1_predictor.db
      - FASTF1_CACHE_DIR=/app/cache
    volumes:
      - ./data:/app/data
      - ./cache:/app/cache
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  api:
    build: .
    command: uvicorn src.api.main:app --host 0.0.0.0 --port 8000
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./data/f1_predictor.db
    volumes:
      - ./data:/app/data
    depends_on:
      - web
    restart: unless-stopped
```

Run with:
```bash
docker-compose up -d
```

### Hugging Face Spaces

Deploy to Hugging Face Spaces for free hosting:

1. Create a new Space at https://huggingface.co/spaces
2. Select "Streamlit" as SDK
3. Upload project files or connect GitHub repository
4. Add secrets in Space settings:
   - `OPENWEATHERMAP_API_KEY` (optional)
   - `FASTF1_CACHE_ENABLED=true`

5. Update `app.py` port configuration:
```python
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 7860))
    # Streamlit handles the rest
```

---

## Quick Start

### Web Interface (Streamlit)

Launch the interactive web application:

```bash
streamlit run app.py --server.port=8501 --server.address=0.0.0.0
```

Navigate to `http://localhost:8501` in your browser.

#### Available Pages:

1. **🏠 Home Dashboard**
   - Upcoming race information
   - Quick prediction widget
   - Recent prediction accuracy
   - Championship standings snapshot

2. **🔮 Race Predictor**
   - Select circuit from dropdown
   - Adjust rain probability slider
   - Set number of simulations
   - Override grid positions (optional)
   - View probability distributions
   - Download results as CSV

3. **⚔️ Head-to-Head**
   - Select two drivers
   - Compare win probabilities
   - View historical matchups
   - Analyze teammate battles

4. **🏆 Championship Forecast**
   - Simulate remaining races
   - Probability of winning championship
   - Points projection charts
   - Constructor standings forecast

5. **📊 Analytics**
   - Driver radar charts
   - Constructor strength trends
   - Circuit analysis
   - Performance decomposition

6. **📄 Report Studio**
   - Generate professional HTML reports
   - Customize chart types
   - Include/exclude sections
   - Export as PDF-ready HTML

### REST API

Start the FastAPI server:

```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

Access API documentation at `http://localhost:8000/docs`

#### Example API Calls:

```bash
# Predict race outcome
curl -X POST "http://localhost:8000/api/v1/predictions/race" \
  -H "Content-Type: application/json" \
  -d '{
    "circuit_id": "monaco",
    "num_simulations": 10000,
    "rain_probability": 0.2
  }'

# Get driver head-to-head
curl -X POST "http://localhost:8000/api/v1/predictions/h2h" \
  -H "Content-Type: application/json" \
  -d '{
    "driver1": "verstappen",
    "driver2": "leclerc",
    "circuit_id": "monza"
  }'

# Get upcoming races
curl "http://localhost:8000/api/v1/circuits/upcoming"

# Get driver list
curl "http://localhost:8000/api/v1/drivers"

# Get championship standings
curl "http://localhost:8000/api/v1/standings/championship"
```

---

## Architecture

### System Design

The project follows a strict layered architecture pattern ensuring separation of concerns and maintainability:

```
┌─────────────────────────────────────────┐
│     PRESENTATION LAYER                  │
│  ┌──────────┐    ┌──────────────────┐  │
│  │Streamlit │    │   FastAPI REST   │  │
│  │  (app.py)│    │  (api/routers/)  │  │
│  └──────────┘    └──────────────────┘  │
└──────────────┬─────────────────────────┘
               │ (HTTP/WebSocket)
┌──────────────▼─────────────────────────┐
│       SERVICE LAYER                    │
│  ┌──────────────────────────────────┐  │
│  │  services/prediction_service.py  │  │
│  │  services/accuracy_service.py    │  │
│  └──────────────────────────────────┘  │
└──────────────┬─────────────────────────┘
               │ (Function calls)
┌──────────────▼─────────────────────────┐
│        ENGINE LAYER                    │
│  ┌──────────────────────────────────┐  │
│  │  engine/predictor.py             │  │
│  │  engine/probability_model.py     │  │
│  │  engine/feature_engineering.py   │  │
│  │  engine/simulation.py            │  │
│  │  engine/calibration.py           │  │
│  └──────────────────────────────────┘  │
└──────────────┬─────────────────────────┘
               │ (Data queries)
┌──────────────▼─────────────────────────┐
│         DATA LAYER                     │
│  ┌────────────┐  ┌──────────────────┐  │
│  │ Static     │  │  Repositories    │  │
│  │ (drivers,  │  │  (DB access,     │  │
│  │ circuits)  │  │   FastF1, Ergast)│  │
│  └────────────┘  └──────────────────┘  │
└────────────────────────────────────────┘
```

### Layer Separation Rules

**CRITICAL ARCHITECTURAL CONSTRAINTS:**

1. **Engine Layer (`src/engine/`)**
   - ✅ Pure computation only
   - ✅ No I/O operations (no file reads, no network calls)
   - ✅ No imports from `api/`, `dashboard/`, or `services/`
   - ✅ Deterministic functions with clear inputs/outputs
   - ❌ Never import Streamlit, FastAPI, or database models

2. **Data Layer (`src/data/`)**
   - ✅ Static reference data (drivers, circuits, teams)
   - ✅ Repository pattern for database access
   - ✅ External API integrations (FastF1, Ergast)
   - ❌ Never import from `engine/`, `api/`, or `dashboard/`

3. **Service Layer (`src/services/`)**
   - ✅ Orchestrates engine and data layers
   - ✅ Business logic and workflow management
   - ✅ Caching and error handling
   - ❌ No presentation logic

4. **Presentation Layer**
   - **Dashboard (`dashboard/`)**: Streamlit UI components
     - ✅ Only imports from `services/`
     - ❌ Never imports directly from `engine/` or `data/`
   - **API (`src/api/`)**: FastAPI routers and schemas
     - ✅ Only imports from `services/`
     - ❌ Never imports directly from `engine/` or `data/`

### Data Flow

```
User Request (Web/API)
         ↓
Service Layer (orchestration, validation)
         ↓
Engine Layer (computation, simulation)
         ↓
Data Layer (static data, DB queries, external APIs)
         ↓
Results flow back up through layers
         ↓
Response to User (JSON, HTML, CSV)
```

### Module Structure

```
FORMULA_1_PREDICTOR_STREAMLIT_2026/
│
├── app.py                          # Streamlit entry point (lazy imports)
├── theme.py                        # UI theme configuration
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Container configuration
├── docker-compose.yml              # Multi-container setup
│
├── src/
│   ├── __init__.py
│   │
│   ├── api/                        # FastAPI application
│   │   ├── __init__.py
│   │   ├── main.py                 # App factory
│   │   ├── routes.py               # Route registration
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── predictions.py      # Prediction endpoints
│   │   │   ├── circuits.py         # Circuit data endpoints
│   │   │   ├── drivers.py          # Driver data endpoints
│   │   │   └── standings.py        # Championship endpoints
│   │   └── schemas/
│   │       ├── __init__.py
│   │       ├── requests.py         # Request models
│   │       └── responses.py        # Response models
│   │
│   ├── config/                     # Configuration management
│   │   ├── __init__.py
│   │   └── settings.py             # Pydantic settings
│   │
│   ├── data/                       # Data layer
│   │   ├── __init__.py
│   │   ├── calendar_2026.py        # 2026 race calendar
│   │   ├── circuit_data.py         # Circuit characteristics
│   │   ├── driver_data.py          # Driver profiles
│   │   ├── driver_traits_database.py # Driver skill attributes
│   │   ├── fastf1_integration.py   # FastF1 API wrapper
│   │   ├── schemas.py              # Data models
│   │   ├── season_2026.py          # Season results tracking
│   │   └── teams.py                # Constructor information
│   │
│   ├── database/                   # Database ORM
│   │   ├── __init__.py
│   │   └── models.py               # SQLAlchemy models
│   │
│   ├── engine/                     # Core prediction engine
│   │   ├── __init__.py
│   │   ├── cache.py                # Thread-safe caching
│   │   ├── calibration.py          # Model calibration
│   │   ├── calibration_state.py    # Calibration state machine
│   │   ├── experiment_tracker.py   # A/B testing framework
│   │   ├── feature_engineering.py  # Feature computation
│   │   ├── multi_dimensional_elo.py # ELO rating system
│   │   ├── optimized_simulation.py # Optimized Monte Carlo
│   │   ├── prediction_tracker.py   # Prediction logging
│   │   ├── predictor.py            # Main prediction interface
│   │   ├── probability_model.py    # Probability distributions
│   │   ├── tire_strategy.py        # Tire degradation model
│   │   ├── validation.py           # Input validation
│   │   ├── vectorized_simulation.py # NumPy vectorized sims
│   │   └── weather_model_v3.py     # Weather impact model
│   │
│   ├── reports/                    # Report generation
│   │   ├── __init__.py
│   │   └── html_report.py          # HTML report builder
│   │
│   └── services/                   # Service layer
│       ├── __init__.py
│       ├── prediction_service.py   # Prediction orchestration
│       ├── accuracy_service.py     # Accuracy tracking
│       └── standings_service.py    # Championship calculations
│
├── tests/                          # Test suite
│   ├── __init__.py
│   ├── test_invariants.py          # Invariant tests
│   ├── test_engine.py              # Engine unit tests
│   ├── test_api.py                 # API integration tests
│   └── test_data.py                # Data layer tests
│
├── scripts/                        # Utility scripts
│   ├── optimize_weights_v3.py      # Hyperparameter optimization
│   ├── data_quality_report.py      # Data validation
│   └── backtest_season.py          # Historical backtesting
│
└── docs/                           # Documentation
    ├── architecture.md             # Architecture details
    └── api_reference.md            # API documentation
```

---

## Core Components

### Prediction Engine

The prediction engine is the heart of the system, located in `src/engine/predictor.py`. It orchestrates the entire prediction pipeline:

```python
from src.engine.predictor import predict, PredictionRequest

# Create prediction request
request = PredictionRequest(
    circuit_id="monaco",
    num_simulations=10000,
    rain_probability=0.3,
    grid_override=None  # Optional: custom starting positions
)

# Run prediction
result = predict(request)

# Access results
print(f"Win probability: {result.driver_probabilities['verstappen']:.2%}")
print(f"Expected position: {result.expected_positions['hamilton']:.1f}")
```

**Key Features:**
- Input validation via Pydantic
- Automatic feature engineering
- Multi-path simulation (vectorized vs optimized)
- Result post-processing and normalization
- Optional database storage

### Feature Engineering

Located in `src/engine/feature_engineering.py`, this module computes all predictive features:

**Computed Features:**

1. **ELO Rating** (`elo_rating`)
   - Multi-dimensional ELO system
   - Separate ratings for qualifying, race pace, wet weather
   - Updated after each session
   - Weight: 0.25

2. **Constructor Strength** (`constructor_strength`)
   - Team performance metric
   - Updated dynamically based on recent races
   - Accounts for car development trajectory
   - Weight: 0.20

3. **Recent Form** (`recent_form`)
   - Exponentially weighted average of last 5 races
   - Handles DNFs appropriately (None, not 0)
   - Decay factor: 0.95 per race
   - Weight: 0.15

4. **Track Type Fit** (`track_type_fit`)
   - Driver/circuit compatibility score
   - Based on historical performance at similar tracks
   - Categories: Street, High-speed, Technical, Mixed
   - Weight: 0.10

5. **Reliability** (`reliability`)
   - Probability of finishing the race
   - Based on driver and constructor DNF history
   - Mechanical failure rates
   - Weight: 0.10

6. **Weather Adjustment** (`weather_adjustment`)
   - Wet weather skill multiplier
   - Rain probability integration
   - Track-specific rain effects
   - Weight: 0.10

7. **Safety Car Upside** (`safety_car_upside`)
   - Probability of benefiting from safety cars
   - Overtaking difficulty at circuit
   - Starting position factor
   - Weight: 0.05

8. **Grid Position** (`grid_position`)
   - Starting position advantage
   - Circuit-specific overtaking difficulty
   - First lap incident probability
   - Weight: 0.05

**Composite Score Calculation:**

```python
composite_score = sum(
    weight * feature_value 
    for weight, feature_value in zip(
        FEATURE_WEIGHTS.values(),
        feature_vector
    )
)
```

### Monte Carlo Simulation

The simulation engine uses vectorized NumPy operations for extreme performance:

**Implementation:** `src/engine/vectorized_simulation.py`

**Algorithm:**
1. Sample driver performance from probability distributions
2. Apply circuit-specific modifiers
3. Simulate lap-by-lap progression
4. Model tire degradation and pit stops
5. Inject random events (safety cars, DNFs)
6. Aggregate results across all simulations

**Performance:**
- 10,000 simulations: ~200ms
- 50,000 simulations: ~800ms
- Memory usage: ~50MB for 50k sims

**Optimization Techniques:**
- Vectorized random number generation
- Broadcasting for batch operations
- Avoiding Python loops
- Efficient memory layout (column-major)

### Calibration System

Ensures prediction accuracy matches reality:

**Location:** `src/engine/calibration.py`

**Calibration States:**
1. **PLACEHOLDER**: Initial state, using default weights
2. **FITTED**: Calibrated on recent data, predictions reliable
3. **STALE**: Data too old, recalibration needed

**Calibration Process:**
```python
from src.engine.calibration import CalibrationManager

manager = CalibrationManager()

# Check calibration status
status = manager.get_status()
if status == "STALE":
    # Recalibrate on last 10 races
    manager.recalibrate(races=range(-10, 0))
```

**Metrics Tracked:**
- Brier Score (probability accuracy)
- Log Loss (information content)
- Calibration Error (predicted vs actual frequencies)
- Sharpness (confidence appropriateness)

### Weather Modeling

Advanced weather impact simulation in `src/engine/weather_model_v3.py`:

**Factors Considered:**
- Rain intensity (light/moderate/heavy)
- Track temperature changes
- Grip level reduction
- Visibility effects
- Tire compound effectiveness
- Driver wet weather skill

**Rain Probability Integration:**
```python
# Convert rain probability to performance impact
wet_performance_multiplier = weather_model.compute_impact(
    rain_probability=0.4,
    driver_wet_skill=0.85,
    circuit_rain_factor=0.7
)
```

### Tire Strategy

Models tire degradation and pit stop decisions:

**Location:** `src/engine/tire_strategy.py`

**Supported Compounds:**
- Soft (fastest, highest degradation)
- Medium (balanced)
- Hard (slowest, lowest degradation)
- Intermediate (wet conditions)
- Full Wet (heavy rain)

**Degradation Model:**
```python
lap_time = base_lap_time * (1 + degradation_rate * laps_on_compound)
```

**Pit Stop Simulation:**
- Fixed time loss: 20-25 seconds
- Undercut potential modeling
- Traffic effects post-pit

### ELO Rating System

Multi-dimensional ELO in `src/engine/multi_dimensional_elo.py`:

**Rating Dimensions:**
1. **Qualifying Pace**: Single-lap speed
2. **Race Pace**: Long-run consistency
3. **Wet Weather**: Performance in rain
4. **Overtaking**: Ability to gain positions
5. **Defense**: Ability to hold positions
6. **Start Quality**: First lap performance

**ELO Update Formula:**
```python
K = 32  # Base K-factor
expected_score = 1 / (1 + 10^((opponent_rating - my_rating) / 400))
actual_score = 1 if won else 0
rating_change = K * (actual_score - expected_score)
new_rating = old_rating + rating_change
```

**Auto-Calibration:**
- K-factor adjusts based on sample size
- New drivers start at 1500 (median)
- Ratings converge after ~20 races

---

## Data Sources

### Static Data

Built-in reference data that doesn't change frequently:

**Location:** `src/data/static/`

**Files:**
- `drivers_2026.py`: 2026 driver lineup with numbers, teams, nationalities
- `circuits_2026.py`: 24 circuits with characteristics (length, turns, DRS zones)
- `constructor_strength.py`: Initial team strength estimates

**Example:**
```python
from src.data.static.drivers_2026 import DRIVERS_2026

print(DRIVERS_2026["verstappen"])
# {'number': 1, 'team': 'red_bull', 'nationality': 'Dutch'}
```

### Dynamic Data Integration

Real-time and historical data from external sources:

#### FastF1 Integration

Official F1 data library for live timing and historical results:

**Location:** `src/data/fastf1_integration.py`

**Capabilities:**
- Live session data (practice, qualifying, race)
- Lap times with sector splits
- Telemetry data (speed, throttle, brake)
- Tire stint information
- Weather data from track sensors
- Radio messages

**Usage:**
```python
from src.data.fastf1_integration import get_session, load_entire_season

# Get specific session
session = get_session(2026, 5, 'Q')  # Round 5, Qualifying

# Load full season
season_data = load_entire_season(2026)
```

**Caching:**
- Session data cached locally in `~/.cache/fastf1/`
- Cache validity: 24 hours for completed sessions
- Live sessions refresh every 30 seconds

#### Ergast API

Historical F1 data (2020-2025):

**Location:** `src/data/repositories/ergast_repository.py`

**Data Available:**
- Historical race results
- Qualifying results
- Driver standings by year
- Constructor standings by year
- Lap times (aggregated)
- Pit stop data

**Usage:**
```python
from src.data.repositories.ergast_repository import ErgastRepository

repo = ErgastRepository()

# Get 2024 championship standings
standings = repo.get_driver_standings(year=2024)

# Get Monaco historical results
monaco_results = repo.get_race_results(circuit_id="monaco", years=range(2020, 2025))
```

---

## Configuration

### Environment Variables

Configure the system via environment variables or `.env` file:

```bash
# Database
F1_DATABASE_URL=sqlite:///./f1_predictor.db

# FastF1 Cache
FASTF1_CACHE_DIR=~/.cache/fastf1
FASTF1_CACHE_ENABLED=true

# OpenWeatherMap API (optional)
OPENWEATHERMAP_API_KEY=your_api_key_here

# Application
LOG_LEVEL=INFO
ENABLE_TELEMETRY=false
MAX_SIMULATIONS=100000
```

Create `.env` file in project root:
```env
F1_DATABASE_URL=sqlite:///./f1_predictor.db
FASTF1_CACHE_ENABLED=true
LOG_LEVEL=DEBUG
```

Load with:
```python
from dotenv import load_dotenv
load_dotenv()
```

### Feature Weights

Adjust the importance of different features in `config/settings.py`:

```python
FEATURE_WEIGHTS = {
    "elo_rating": 0.25,
    "constructor_strength": 0.20,
    "recent_form": 0.15,
    "track_type_fit": 0.10,
    "reliability": 0.10,
    "weather_adjustment": 0.10,
    "safety_car_upside": 0.05,
    "grid_position": 0.05,
}

# Must sum to 1.0
assert sum(FEATURE_WEIGHTS.values()) == 1.0
```

**Tuning Guidelines:**
- Increase `elo_rating` if individual driver skill is most predictive
- Increase `constructor_strength` if car performance dominates
- Increase `recent_form` for mid-season predictions
- Increase `weather_adjustment` for rainy races

### Simulation Parameters

Control simulation behavior:

```python
SIMULATION_CONFIG = {
    "default_sims": 10000,
    "max_sims": 100000,
    "min_sims": 1000,
    "random_seed": None,  # None = random, int = reproducible
    "use_vectorized": True,  # Use NumPy vectorization
    "parallel_workers": 4,  # For non-vectorized path
}
```

---

## Usage Examples

### Basic Race Prediction

Predict the outcome of the Monaco Grand Prix:

```python
from src.engine.predictor import predict, PredictionRequest

request = PredictionRequest(
    circuit_id="monaco",
    num_simulations=10000,
    rain_probability=0.15
)

result = predict(request)

# Print top 5 win probabilities
sorted_drivers = sorted(
    result.driver_probabilities.items(),
    key=lambda x: x[1],
    reverse=True
)[:5]

for driver, prob in sorted_drivers:
    print(f"{driver}: {prob:.2%}")
```

**Output:**
```
verstappen: 28.45%
leclerc: 22.10%
norris: 15.30%
hamilton: 12.80%
sainz: 8.95%
```

### Head-to-Head Comparison

Compare Verstappen vs Leclerc at Monaco:

```python
from src.services.prediction_service import PredictionService

service = PredictionService()

h2h_result = service.head_to_head(
    driver1="verstappen",
    driver2="leclerc",
    circuit_id="monaco",
    num_simulations=10000
)

print(f"Verstappen wins: {h2h_result.driver1_win_prob:.2%}")
print(f"Leclerc wins: {h2h_result.driver2_win_prob:.2%}")
print(f"Neither wins: {h2h_result.neither_wins_prob:.2%}")
```

### Championship Forecast

Simulate the remainder of the 2026 season:

```python
from src.services.standings_service import StandingsService

service = StandingsService()

forecast = simulate_championship(
    current_standings=get_current_standings(),
    remaining_races=get_remaining_races(),
    num_simulations=5000
)

# Probability of each driver winning championship
for driver, prob in forecast.championship_probabilities.items():
    print(f"{driver}: {prob:.2%}")
```

### Constructor Analysis

Analyze team performance:

```python
from src.engine.feature_engineering import compute_constructor_metrics

metrics = compute_constructor_metrics(team="red_bull", season=2026)

print(f"Average qualifying position: {metrics.avg_qualifying:.2f}")
print(f"Average race finish: {metrics.avg_finish:.2f}")
print(f"Reliability rate: {metrics.reliability:.2%}")
print(f"Points per race: {metrics.points_per_race:.1f}")
```

### HTML Report Generation

Create a professional report:

```python
from src.reports.html_report import generate_report

report_html = generate_report(
    circuit_id="spa",
    num_simulations=10000,
    rain_probability=0.4,
    include_sections=[
        "win_probabilities",
        "podium_probabilities",
        "dnf_risks",
        "value_bets",
        "head_to_head",
        "circuit_analysis"
    ]
)

# Save to file
with open("spa_report.html", "w") as f:
    f.write(report_html)

# Open in browser
import webbrowser
webbrowser.open('spa_report.html')
```

### Backtesting Example:**

Test prediction accuracy on historical data using Python:

```python
from src.services.prediction_service import PredictionService
from src.data.calendar_2026 import get_races_for_year

service = PredictionService()

# Backtest entire 2024 season
races = get_races_for_year(2024)
results = []

for race in races:
    prediction = service.predict_race(
        circuit_id=race.circuit_id,
        num_simulations=5000
    )
    # Compare with actual results
    actual = service.get_actual_results(race.id)
    accuracy = service.calculate_accuracy(prediction, actual)
    results.append(accuracy)

# Generate accuracy report
avg_brier_score = sum(r.brier_score for r in results) / len(results)
print(f"Avg Brier Score: {avg_brier_score:.3f}")
```

**Sample Output:**
```
Backtest Results - 2024 Season
================================
Total Races: 24
Avg Brier Score: 0.142
Avg Log Loss: 0.456
Win Prediction Accuracy: 41.7% (10/24 correct)
Podium Prediction Accuracy: 68.3%
Top 10 Prediction Accuracy: 82.1%
```

---

## Prediction Methodology

### Probability Model

The core probability model transforms feature scores into win probabilities:

**Step 1: Compute Composite Scores**
```python
score_i = Σ (weight_j × feature_ij) for all features j
```

**Step 2: Apply Logistic Transformation**
```python
raw_probability_i = exp(score_i) / Σ exp(score_k) for all drivers k
```

**Step 3: Enforce Constraints**
```python
# Ensure P(win) ≤ P(podium) ≤ P(points)
for driver in drivers:
    if driver.p_win > driver.p_podium:
        driver.p_podium = driver.p_win
    if driver.p_podium > driver.p_points:
        driver.p_points = driver.p_podium
```

**Step 4: Normalize**
```python
# Ensure probabilities sum to 1
total = sum(driver.p_win for driver in drivers)
for driver in drivers:
    driver.p_win /= total
```

### Multi-Dimensional ELO

Extends traditional ELO to multiple performance dimensions:

**Initialization:**
- New drivers: 1500 in all dimensions
- Experienced drivers: Historical average

**Update After Race:**
```python
for dimension in [qualifying, race_pace, wet_weather, ...]:
    expected = logistic(opponent_rating - driver_rating)
    actual = 1 if driver_outperformed else 0
    delta = K_factor × (actual - expected)
    driver_rating += delta
    opponent_rating -= delta
```

**K-Factor Scheduling:**
- New drivers (< 5 races): K = 50
- Developing drivers (5-20 races): K = 32
- Established drivers (> 20 races): K = 16

### Vectorized Simulation

Uses NumPy broadcasting for massive parallelism:

**Traditional Loop (Slow):**
```python
results = []
for sim in range(10000):
    result = simulate_one_race()
    results.append(result)
```

**Vectorized (Fast):**
```python
# Generate all random numbers at once
performance_samples = np.random.normal(
    loc=driver_scores,
    scale=noise_level,
    size=(10000, num_drivers)
)

# Compute all results simultaneously
finishing_orders = np.argsort(-performance_samples, axis=1)
```

**Speed Improvement:** 50-100x faster than loop-based approach

### Confidence Intervals

Quantifies prediction uncertainty:

**Method:** Bootstrap resampling of simulation results

**Calculation:**
```python
from scipy import stats

# Extract win counts from simulations
win_counts = np.bincount(simulation_winners, minlength=num_drivers)

# Compute 95% confidence interval
ci_lower, ci_upper = stats.beta.interval(
    0.95,
    win_counts + 1,
    num_sims - win_counts + 1
)
```

**Interpretation:**
- Narrow CI: High confidence in prediction
- Wide CI: High uncertainty, more simulations recommended

### DNF Risk Assessment

Models probability of Did Not Finish:

**Factors:**
1. Driver historical DNF rate
2. Constructor reliability
3. Circuit danger level (Monaco > Silverstone)
4. Weather conditions (rain increases DNF risk)
5. Starting position (first lap incidents)

**Formula:**
```python
dnf_probability = base_dnf_rate × circuit_factor × weather_factor × position_factor

# Typical values
base_dnf_rate: 0.05-0.15 per race
circuit_factor: 0.8-1.5
weather_factor: 1.0 (dry) to 2.5 (heavy rain)
position_factor: 1.5 (P1) to 0.8 (P20)
```

---

## Performance Optimization

### Caching Strategy

Multi-level caching for optimal performance:

**Level 1: In-Memory Cache**
- Thread-safe dictionary cache
- TTL: 5 minutes for dynamic data
- Invalidated on new race results

**Level 2: Disk Cache (FastF1)**
- Session data cached locally
- Persistent across restarts
- Size limit: 2 GB

**Level 3: Database Cache**
- Prediction results stored in SQLite
- Queryable for historical analysis
- Automatic cleanup after 90 days

**Cache Hit Rates:**
- Circuit data: 99%+ (rarely changes)
- Driver ELO: 95%+ (updated weekly)
- Predictions: 70%+ (depends on parameter variation)

### Parallel Processing

For non-vectorized simulations:

```python
from concurrent.futures import ProcessPoolExecutor

def run_batch(batch_size):
    return [simulate_one_race() for _ in range(batch_size)]

with ProcessPoolExecutor(max_workers=4) as executor:
    batches = [10000 // 4] * 4
    results = list(executor.map(run_batch, batches))
```

**Speedup:** ~3.5x on 4-core CPU (less than linear due to overhead)

### Memory Management

Optimize memory usage for large simulations:

**Techniques:**
1. Use `float32` instead of `float64` where precision allows
2. Process simulations in batches
3. Delete intermediate arrays explicitly
4. Use generators for lazy evaluation

**Memory Profile:**
- 10k simulations: ~50 MB
- 50k simulations: ~200 MB
- 100k simulations: ~400 MB

**Recommendation:** Use 50k simulations for balance of accuracy and memory

---

## Testing

### Unit Tests

Test individual components in isolation:

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_engine.py -v

# Run with coverage
pytest tests/ --cov=src/engine --cov-report=html
```

**Test Coverage Goals:**
- Engine layer: > 90%
- Data layer: > 85%
- API layer: > 80%
- Dashboard: > 70%

### Integration Tests

Test component interactions:

```python
def test_full_prediction_pipeline():
    """Test complete prediction flow from request to result"""
    request = PredictionRequest(circuit_id="monaco", num_simulations=1000)
    result = predict(request)
    
    assert len(result.driver_probabilities) == 20
    assert abs(sum(result.driver_probabilities.values()) - 1.0) < 0.01
    assert all(0 <= p <= 1 for p in result.driver_probabilities.values())
```

### Invariant Testing

Ensure mathematical properties hold:

**Location:** `tests/test_invariants.py`

**Invariants Checked:**
1. Probabilities sum to 1.0
2. P(win) ≤ P(podium) ≤ P(points) for each driver
3. All probabilities between 0 and 1
4. Expected positions are consistent with win probabilities
5. DNF probabilities reasonable (0.01 - 0.30)

```bash
# Run invariant tests
pytest tests/test_invariants.py -v
```

---

## Database Schema

### Tables Overview

SQLite database with the following tables:

**1. drivers**
```sql
CREATE TABLE drivers (
    id INTEGER PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,
    first_name TEXT,
    last_name TEXT,
    number INTEGER UNIQUE,
    nationality TEXT,
    date_of_birth DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**2. constructors**
```sql
CREATE TABLE constructors (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    nationality TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**3. circuits**
```sql
CREATE TABLE circuits (
    id INTEGER PRIMARY KEY,
    circuit_id TEXT UNIQUE NOT NULL,
    name TEXT,
    location TEXT,
    country TEXT,
    length_km REAL,
    num_turns INTEGER,
    drs_zones INTEGER
);
```

**4. races**
```sql
CREATE TABLE races (
    id INTEGER PRIMARY KEY,
    year INTEGER NOT NULL,
    round INTEGER NOT NULL,
    circuit_id TEXT REFERENCES circuits(circuit_id),
    race_name TEXT,
    race_date DATE,
    UNIQUE(year, round)
);
```

**5. qualifying_results**
```sql
CREATE TABLE qualifying_results (
    id INTEGER PRIMARY KEY,
    race_id INTEGER REFERENCES races(id),
    driver_id INTEGER REFERENCES drivers(id),
    position INTEGER,
    q1_time TIME,
    q2_time TIME,
    q3_time TIME
);
```

**6. race_results**
```sql
CREATE TABLE race_results (
    id INTEGER PRIMARY KEY,
    race_id INTEGER REFERENCES races(id),
    driver_id INTEGER REFERENCES drivers(id),
    grid_position INTEGER,
    finish_position INTEGER,
    points INTEGER,
    status TEXT,  -- 'Finished', 'DNF', 'DNS', etc.
    fastest_lap TIME,
    time_gap INTERVAL
);
```

**7. predictions**
```sql
CREATE TABLE predictions (
    id INTEGER PRIMARY KEY,
    race_id INTEGER REFERENCES races(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    num_simulations INTEGER,
    rain_probability REAL,
    results_json TEXT  -- JSON-encoded prediction results
);
```

**8. elo_ratings**
```sql
CREATE TABLE elo_ratings (
    id INTEGER PRIMARY KEY,
    driver_id INTEGER REFERENCES drivers(id),
    dimension TEXT,  -- 'qualifying', 'race_pace', etc.
    rating REAL DEFAULT 1500.0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(driver_id, dimension)
);
```

### Migration Guide

Initialize or update database:

```python
# Fresh installation
from src.database.models import init_db
init_db()

# Or using the API service
from src.services.prediction_service import PredictionService
service = PredictionService()
service.initialize_database()
```

**Migration Files:** Located in `src/database/migrations/`

---

## API Documentation

### Endpoints

Base URL: `http://localhost:8000/api/v1`

#### Predictions

**POST /predictions/race**
Predict race outcome

Request:
```json
{
  "circuit_id": "monaco",
  "num_simulations": 10000,
  "rain_probability": 0.2,
  "grid_override": null
}
```

Response:
```json
{
  "circuit_id": "monaco",
  "driver_probabilities": {
    "verstappen": 0.2845,
    "leclerc": 0.2210,
    ...
  },
  "expected_positions": {
    "verstappen": 2.1,
    "leclerc": 2.8,
    ...
  },
  "dnf_probabilities": {
    "verstappen": 0.05,
    "leclerc": 0.08,
    ...
  }
}
```

**POST /predictions/h2h**
Head-to-head comparison

Request:
```json
{
  "driver1": "verstappen",
  "driver2": "leclerc",
  "circuit_id": "monaco"
}
```

Response:
```json
{
  "driver1": "verstappen",
  "driver2": "leclerc",
  "driver1_win_prob": 0.52,
  "driver2_win_prob": 0.41,
  "neither_wins_prob": 0.07
}
```

#### Circuits

**GET /circuits**
List all circuits

Response:
```json
[
  {
    "circuit_id": "monaco",
    "name": "Circuit de Monaco",
    "location": "Monte Carlo",
    "country": "Monaco"
  },
  ...
]
```

**GET /circuits/upcoming**
Get upcoming races

Response:
```json
[
  {
    "round": 6,
    "circuit_id": "silverstone",
    "race_name": "British Grand Prix",
    "race_date": "2026-07-05"
  },
  ...
]
```

#### Drivers

**GET /drivers**
List all drivers

Response:
```json
[
  {
    "code": "VER",
    "first_name": "Max",
    "last_name": "Verstappen",
    "number": 1,
    "team": "Red Bull Racing"
  },
  ...
]
```

#### Standings

**GET /standings/championship**
Current championship standings

Response:
```json
{
  "driver_standings": [
    {"position": 1, "driver": "verstappen", "points": 125},
    {"position": 2, "driver": "leclerc", "points": 98},
    ...
  ],
  "constructor_standings": [
    {"position": 1, "constructor": "red_bull", "points": 210},
    ...
  ]
}
```

### Request/Response Schemas

All schemas defined in `src/api/schemas/`:

**Request Models:** `requests.py`
- `PredictionRequest`
- `H2HRequest`
- `ChampionshipForecastRequest`

**Response Models:** `responses.py`
- `PredictionResponse`
- `H2HResponse`
- `DriverListResponse`
- `CircuitListResponse`
- `StandingsResponse`

### Authentication

Currently, the API is open (no authentication required).

**Future Enhancement:** JWT-based authentication planned for production deployments.

Enable authentication:
```bash
export ENABLE_AUTH=true
export JWT_SECRET_KEY=your_secret_key
```

---

## Deployment

### Production Setup

**Recommended Stack:**
- Web Server: Nginx (reverse proxy)
- Application Server: Gunicorn (Streamlit) + Uvicorn (FastAPI)
- Database: PostgreSQL (instead of SQLite for concurrency)
- Cache: Redis (for distributed caching)
- Monitoring: Prometheus + Grafana

**Docker Compose Production:**

```yaml
version: '3.8'

services:
  nginx:
    image: nginx:latest
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - streamlit
      - api

  streamlit:
    build: .
    command: gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8501 app:server
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/f1predictor
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  api:
    build: .
    command: uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/f1predictor
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=f1predictor
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Nginx Configuration

`nginx.conf`:
```nginx
events {
    worker_connections 1024;
}

http {
    upstream streamlit {
        server streamlit:8501;
    }

    upstream api {
        server api:8000;
    }

    server {
        listen 80;
        server_name f1predictor.example.com;

        location / {
            proxy_pass http://streamlit;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        location /api/ {
            proxy_pass http://api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
```

### Monitoring

**Health Checks:**

Streamlit:
```bash
curl http://localhost:8501/_stcore/health
```

FastAPI:
```bash
curl http://localhost:8000/health
```

**Metrics to Monitor:**
- Prediction latency (target: < 2 seconds)
- API response time (target: < 500ms)
- Database connection pool usage
- Cache hit rates
- Error rates (5xx responses)
- Memory usage
- CPU utilization

**Alerting Thresholds:**
- Prediction latency > 5 seconds
- Error rate > 1%
- Memory usage > 80%
- Database connections > 90% capacity

---

## Troubleshooting

### Common Issues

**Issue 1: "No module named 'src'"**

Solution: Ensure you're running from project root and Python can find the src package.

```bash
# Check current directory
pwd

# Should be: c:\Users\PC\Music\FORMULA_1_PREDICTOR_STREAMLIT_2026

# If not, navigate there
cd c:\Users\PC\Music\FORMULA_1_PREDICTOR_STREAMLIT_2026

# Verify src directory exists
ls src/
```

**Issue 2: FastF1 data not loading**

Solution: Check internet connection and FastF1 cache.

```bash
# Clear FastF1 cache
rm -rf ~/.cache/fastf1/*

# Retry with verbose logging
python -c "import fastf1; fastf1.Cache.enable_cache('./cache'); session = fastf1.get_session(2026, 5, 'R'); session.load()"
```

**Issue 3: Database locked errors**

Solution: SQLite doesn't handle concurrent writes well.

```bash
# Switch to PostgreSQL for production
export F1_DATABASE_URL=postgresql://user:pass@localhost:5432/f1predictor

# Or reduce concurrent predictions
export MAX_CONCURRENT_PREDICTIONS=1
```

**Issue 4: Out of memory during large simulations**

Solution: Reduce simulation count or increase batch processing.

```python
# Instead of 100k sims at once
result = predict(PredictionRequest(circuit_id="monaco", num_simulations=100000))

# Use 50k sims (better accuracy/memory tradeoff)
result = predict(PredictionRequest(circuit_id="monaco", num_simulations=50000))
```

**Issue 5: Slow prediction times**

Solution: Enable vectorized simulation and check CPU usage.

```python
# Ensure vectorized path is enabled
from src.config.settings import settings
settings.SIMULATION_CONFIG["use_vectorized"] = True

# Check if NumPy is using BLAS
import numpy as np
np.__config__.show()  # Should show MKL or OpenBLAS
```

### Debug Mode

Enable detailed logging:

```bash
export LOG_LEVEL=DEBUG
streamlit run app.py
```

View logs:
```bash
# Streamlit logs appear in terminal
# FastAPI logs in uvicorn output

# For file logging
export LOG_FILE=prediction.log
```

### Log Analysis

**Log Levels:**
- DEBUG: Detailed diagnostic information
- INFO: General operational messages
- WARNING: Unexpected but handled situations
- ERROR: Serious problems requiring attention
- CRITICAL: System failures

**Example Log Entry:**
```
2026-06-09 18:15:32 INFO [predictor] Starting prediction for monaco (10000 sims, rain=0.2)
2026-06-09 18:15:32 DEBUG [feature_engineering] Computing features for 20 drivers
2026-06-09 18:15:33 INFO [simulation] Running 10000 vectorized simulations
2026-06-09 18:15:33 DEBUG [simulation] Simulation completed in 0.245s
2026-06-09 18:15:33 INFO [predictor] Prediction complete. Winner: verstappen (28.4%)
```

---

## Roadmap

### Version 5.1 (Q3 2026)
- [ ] Real-time prediction updates during races
- [ ] Mobile app (React Native)
- [ ] Telegram bot integration
- [ ] Enhanced tire strategy visualization

### Version 5.2 (Q4 2026)
- [ ] Machine learning model integration (XGBoost/LightGBM)
- [ ] Automated hyperparameter tuning with Optuna
- [ ] Driver fatigue modeling
- [ ] Team radio sentiment analysis

### Version 6.0 (2027 Season)
- [ ] Multi-year forecasting
- [ ] Regulation change impact modeling
- [ ] Junior driver promotion predictions
- [ ] Transfer market analysis

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

**Development Workflow:**
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes following architecture rules
4. Add tests for new functionality
5. Ensure all tests pass (`pytest tests/ -v`)
6. Commit changes (`git commit -m 'Add amazing feature'`)
7. Push to branch (`git push origin feature/amazing-feature`)
8. Open Pull Request

**Code Style:**
- Follow PEP 8
- Use type hints
- Write docstrings (Google style)
- Keep functions small and focused
- No cross-layer imports

**Testing Requirements:**
- All new features must have tests
- Maintain > 80% code coverage
- Include invariant tests for probability models

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## Acknowledgments

**Libraries & Tools:**
- [Streamlit](https://streamlit.io/) - Beautiful web apps in Python
- [FastF1](https://github.com/theOehrly/Fast-F1) - Official F1 data library
- [NumPy](https://numpy.org/) - Numerical computing
- [Pandas](https://pandas.pydata.org/) - Data analysis
- [Plotly](https://plotly.com/) - Interactive visualizations
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - Database toolkit

**Data Sources:**
- Formula 1 Official Timing Data
- Ergast Developer API
- OpenWeatherMap API

**Community:**
- F1 technical community on Reddit (r/formula1)
- FastF1 Discord server
- Streamlit community forum

**Special Thanks:**
- All contributors who have helped improve this project
- The F1 data community for pioneering work in motorsport analytics
- Beta testers who provided valuable feedback

---

## Contact & Support

**Issues:** Report bugs or request features on GitHub Issues

**Discussions:** Join community discussions on GitHub Discussions

**Email:** For business inquiries: contact@f1predictor.com (placeholder)

**Twitter:** [@F1Predictor](https://twitter.com/f1predictor) (placeholder)

---

<div align="center">

**Made with ❤️ for F1 fans worldwide**

[⭐ Star this repository](#) • [🐛 Report Bug](#) • [💡 Request Feature](#)

</div>