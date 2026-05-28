# 🏁 F1MLpredictions2026 - Streamlit Edition
### Probabilistic F1 Race Predictions + Live FastF1 Analytics

> Interactive web dashboard combining Monte Carlo race predictions with real-time Formula 1 data via FastF1.

---

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Launch dashboard
streamlit run app.py

# Or use CLI
python app.py predict --race canada
python app.py circuits
python app.py api --port 8000
```

**Opens at:** http://localhost:8501

---

## ✨ Features

### 🏁 Race Predictions
- Monte Carlo simulations (1K-20K runs)
- Win/Podium/Points/DNF probabilities
- Rain & grid position overrides
- Downloadable CSV results

### 📊 Live F1 Data (FastF1)
- Real lap times from any session
- Telemetry: speed, throttle, brake, RPM
- Weather conditions
- Sector time analysis

### 👤 Driver Analytics
- Season performance tracking
- Teammate head-to-head comparisons
- Qualifying vs race performance
- Historical results

### 🏎️ Circuit Analysis
- Track characteristics
- Historical winners
- Team dominance patterns
- Lap time comparisons

### ⚖️ Driver Comparisons
- Side-by-side telemetry overlays
- Speed traces
- Throttle/brake patterns
- Season battle tracking

---

## 🛠️ Installation

### Prerequisites
- Python 3.10+

### Setup

```bash
# Create virtual environment
py -m venv .venv          # Windows
python3 -m venv .venv     # Mac/Linux

.venv\Scripts\activate    # Windows
source .venv/bin/activate # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Launch
streamlit run app.py
```

---

## 🎮 Dashboard Pages

### 1. Race Predictions
Select circuit → Adjust settings → Run prediction → View results

**Controls:**
- Rain probability slider (0-100%)
- Simulation count (1K-20K)
- Grid position overrides
- CSV export

### 2. Live Race Data
Browse real F1 data from FastF1

**Features:**
- Session selector (P1/P2/P3/Q/R)
- Lap time evolution charts
- Weather visualization
- Fastest lap analysis

### 3. Driver Analytics
Deep dive into driver performance

**Analysis:**
- Points progression
- Season statistics
- Teammate battles
- Race craft evaluation

### 4. Circuit Analysis
Track-specific insights

**Data:**
- Circuit characteristics radar
- Historical winners
- Performance metrics
- Team success patterns

### 5. Comparisons
Head-to-head driver battles

**Telemetry Overlays:**
- Speed traces
- Throttle application
- Brake usage
- RPM throughout lap
- Gear changes

---

## 💻 Command Line Interface

### Predictions

```bash
# Basic prediction
python app.py predict --race canada

# With options
python app.py predict --race monaco --rain 0.70 --sims 10000

# Post-qualifying (actual grid)
python app.py predict --race canada \
  --grid-override "antonelli:1,russell:2"

# JSON output
python app.py predict --race canada --json-out

# Auto-generate HTML report
python app.py predict --race canada --auto-report
```

### Utilities

```bash
# List circuits
python app.py circuits

# Quality check
python app.py quality-check

# Start API
python app.py api --port 8000
```

### CLI Options

| Flag | Description | Example |
|------|-------------|---------|
| `--race` | Circuit ID | `--race canada` |
| `--rain` | Rain prob (0-1) | `--rain 0.65` |
| `--sims` | Simulations | `--sims 10000` |
| `--seed` | Random seed | `--seed 42` |
| `--grid-override` | Grid positions | `"VER:1,HAM:2"` |
| `--json-out` | JSON format | (flag) |
| `--auto-report` | HTML report | (flag) |

---

## 🌐 REST API

Start server:
```bash
python app.py api --port 8000
```

Docs: http://localhost:8000/docs

### Endpoints

**Predictions:**
```
GET  /api/v1/predict/{circuit_id}
GET  /api/v1/predict/{circuit_id}/winner
GET  /api/v1/predict/{circuit_id}/dnf
POST /api/v1/simulate
```

**Data:**
```
GET /api/v1/standings/drivers
GET /api/v1/standings/constructors
GET /api/v1/circuits
GET /api/v1/drivers
GET /api/v1/health
```

**Example:**
```bash
curl http://localhost:8000/api/v1/predict/canada?rain_probability=0.6
```

---

## 🧠 How Predictions Work

### 4-Layer Pipeline

**1. Feature Engineering (8 Signals)**
- ELO rating (driver skill)
- Constructor strength (car performance)
- Recent form (momentum)
- Track type fit (style match)
- Grid position (starting advantage)
- Reliability (DNF risk)
- Weather adjustment (wet skill)
- Safety car upside (chaos benefit)

**2. Composite Score**
Weighted combination of all 8 signals

**3. Monte Carlo Simulation**
5,000+ simulated races with random chaos

**4. Platt Calibration**
Adjust probabilities using historical data

### Key Principles

✅ **Anti-Leakage**: Only pre-race data used  
✅ **Transparency**: All factors visible  
✅ **Calibration**: Probabilities are honest  
✅ **Interpretability**: Clear reasoning  

---

## 🏎️ FastF1 Integration

### Data Access

Real-time F1 data including:
- Session results (P1/P2/P3/Q/R)
- Lap times and sector splits
- Telemetry (speed, throttle, brake, RPM, gear)
- Weather conditions
- Driver profiles
- Team information

### Caching

- **FastF1 cache**: `.fastf1_cache` (persistent)
- **Streamlit cache**: `@st.cache_data` (TTL-based)
- **Session state**: User interactions

First load downloads data (slow). Subsequent loads use cache (fast).

---

## 🗺️ Available Circuits (2026)

24 races in the 2026 season:

`australia`, `china`, `japan`, `bahrain`, `saudi_arabia`, `miami`, `canada`, `monaco`, `spain`, `austria`, `britain`, `hungary`, `belgium`, `netherlands`, `italy`, `madrid`, `azerbaijan`, `singapore`, `usa`, `mexico`, `brazil`, `las_vegas`, `qatar`, `uae`

Use these IDs with `--race` flag or API calls.

---

## 🌐 Deployment

### Streamlit Cloud (FREE)
1. Create account at [streamlit.io/cloud](https://streamlit.io/cloud)
2. Connect your repository
3. Deploy!

### Docker
```bash
docker build -t f1-dashboard .
docker run -p 8501:8501 f1-dashboard
```

### Heroku
```bash
heroku create your-app
# Deploy your code to Heroku
```

### VPS
Install on Ubuntu/AWS/DigitalOcean and run with nginx reverse proxy.

See full deployment guide in documentation.

---

## 📂 Project Structure

```
F1MLpredictions2-streamlit/
├── app.py                    # Unified entry (CLI + Streamlit + API)
├── fastf1_integration.py     # FastF1 data layer
│
├── pages/                    # Dashboard pages
│   ├── predictions.py
│   ├── live_data.py
│   ├── driver_analytics.py
│   ├── circuit_analysis.py
│   └── comparisons.py
│
├── engine/                   # Prediction engine
│   ├── predictor.py
│   ├── probability_model.py
│   ├── feature_engineering.py
│   └── calibration.py
│
├── data/                     # F1 data
│   ├── driver_data.py
│   ├── circuit_data.py
│   ├── season_2026.py
│   └── calendar_2026.py
│
├── api/                      # REST API
│   ├── routes.py
│   └── schemas.py
│
├── config/                   # Settings
│   └── settings.py
│
├── scripts/                  # Utilities
│   ├── post_race_update.py
│   ├── recalibrate_model.py
│   └── ingest_f1_data.py
│
├── tests/                    # Unit tests
├── reports/                  # HTML reports
├── .streamlit/               # Streamlit config
├── requirements.txt
└── README.md
```

---

## 🔧 Keeping Data Updated

### After Each Race

```bash
# Add results
python scripts/post_race_update.py \
  --round 5 --circuit canada \
  --results "antonelli:1,russell:2,norris:3"

# Update data/season_2026.py with generated code
```

### Automated Sync

```bash
python scripts/ingest_f1_data.py
```

Auto-fetches from Jolpica-F1, FastF1, and OpenF1 APIs.

---

## 📐 Model Accuracy

### Metrics

- **Brier Score**: < 0.040 (target)
- **Log-Loss**: < 0.15 (target)
- **RPS**: < 0.25 (target)

### Baseline Comparison

| Method | Brier Score |
|--------|-------------|
| Random | ~0.048 |
| Grid-only | ~0.042 |
| **Our Model** | **< 0.040** |

Check accuracy:
```bash
python scripts/recalibrate_model.py
```

---

## ❓ Troubleshooting

### Common Issues

**Module not found:**
```bash
pip install -r requirements.txt
```

**Slow loading:**
- First load downloads FastF1 data (normal)
- Clear cache: `rm -rf .fastf1_cache`

**Charts not showing:**
```bash
pip install --upgrade plotly
```

**FastF1 error:**
- Check internet connection
- APIs may be temporarily down
- Retry after few minutes

**App won't start:**
```bash
python --version  # Need 3.10+
pip install -r requirements.txt
```

---

## ⚡ Performance Tips

- Enable caching (automatic)
- Use recent seasons only
- Limit simulation count for quick checks
- Sample historical data
- Store large datasets in session state

---

## 🛠️ Technology Stack

| Technology | Purpose |
|------------|---------|
| Python 3.10+ | Language |
| Streamlit 1.31+ | Web UI |
| FastF1 3.1+ | F1 data |
| Plotly 5.18+ | Visualizations |
| FastAPI 0.111+ | REST API |
| Pandas 2.2+ | Data processing |
| NumPy 1.26+ | Computing |
| scikit-learn 1.4+ | ML calibration |

---

## 🤝 Contributing

Contributions welcome!

Areas of interest:
- New visualizations
- Improved prediction models
- UI/UX enhancements
- Bug fixes
- Documentation

---

## 📊 Use Cases

**F1 Fans:** Pre-race predictions, driver comparisons  
**Data Analysts:** Export data, study patterns  
**Content Creators:** Charts for videos, storylines  
**Fantasy Players:** Form tracking, circuit analysis  
**Students:** Learn data science with real F1 data  

---

## 📈 Future Enhancements

- [ ] Live race weekend tracking
- [ ] Betting odds integration
- [ ] Fantasy F1 recommendations
- [ ] Tire strategy optimizer
- [ ] Weather impact predictions
- [ ] Mobile app
- [ ] Social sharing

---

## 📞 Support

- **Issues:** Contact project maintainer
- **Questions:** Check documentation
- **Docs:** This README

---

## 🙏 Acknowledgments

- **FastF1 Team:** F1 data access library
- **Streamlit Team:** Web framework
- **Original Contributors:** Prediction engine foundation
- **Formula 1:** The sport we love

---

**Built with ❤️ for F1 fans**

*Version 2.0 - Streamlit + FastF1 Edition*
