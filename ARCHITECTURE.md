# 🏗️ System Architecture Diagram

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    User's Web Browser                            │
│                   (http://localhost:8501)                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTP/WebSocket
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                  Streamlit Server                                │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              streamlit_app.py (Main Entry)                │  │
│  │  - Navigation routing                                     │  │
│  │  - Custom CSS styling                                     │  │
│  │  - Sidebar controls                                       │  │
│  └────────────────┬─────────────────────────────────────────┘  │
│                   │                                              │
│  ┌────────────────▼─────────────────────────────────────────┐  │
│  │                   Pages Layer                             │  │
│  │                                                           │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │  │
│  │  │ predictions  │  │  live_data   │  │   driver_    │  │  │
│  │  │    .py       │  │     .py      │  │  analytics   │  │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │  │
│  │                                                           │  │
│  │  ┌──────────────┐  ┌──────────────┐                     │  │
│  │  │  circuit_    │  │ comparisons  │                     │  │
│  │  │  analysis    │  │     .py      │                     │  │
│  │  └──────────────┘  └──────────────┘                     │  │
│  └────────────────┬─────────────────────────────────────────┘  │
│                   │                                              │
│  ┌────────────────▼─────────────────────────────────────────┐  │
│  │              Data Access Layer                            │  │
│  │                                                           │  │
│  │  ┌────────────────────────┐  ┌──────────────────────┐   │  │
│  │  │ fastf1_integration.py  │  │  Existing Engine     │   │  │
│  │  │  - Session loading     │  │  - predictor.py      │   │  │
│  │  │  - Lap times           │  │  - probability_model │   │  │
│  │  │  - Telemetry           │  │  - feature_engineer  │   │  │
│  │  │  - Weather data        │  │  - calibration       │   │  │
│  │  │  - Driver info         │  └──────────────────────┘   │  │
│  │  └────────┬───────────────┘                              │  │
│  └───────────┼──────────────────────────────────────────────┘  │
└──────────────┼──────────────────────────────────────────────────┘
               │
     ┌─────────┴──────────┐
     │                    │
     ▼                    ▼
┌─────────────┐   ┌──────────────────┐
│  FastF1 API │   │  Internal Data   │
│  (External) │   │  (Local Files)   │
│             │   │                  │
│ - Sessions  │   │ - driver_data.py │
│ - Laps      │   │ - circuit_data   │
│ - Telemetry │   │ - season_2026    │
│ - Weather   │   │ - calendar_2026  │
│ - Results   │   │ - config/        │
└─────────────┘   └──────────────────┘
```

---

## Data Flow Diagrams

### 1. Race Prediction Flow

```
User Action: Select circuit + settings
         │
         ▼
┌─────────────────────┐
│  predictions.py     │
│  - Get user inputs  │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  PredictionRequest  │
│  - circuit_id       │
│  - rain_probability │
│  - n_simulations    │
│  - grid_overrides   │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ engine/predictor.py │
│  predict() function │
└────────┬────────────┘
         │
         ├──────────────────┐
         │                  │
         ▼                  ▼
┌─────────────────┐ ┌────────────────────┐
│feature_engineer │ │ get_circuit()      │
│- ELO scores     │ │ - SC probability   │
│- Constructor    │ │ - Rain probability │
│- Recent form    │ │ - Lap count        │
│- Track fit      │ └────────────────────┘
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ probability_model.py    │
│ Monte Carlo Simulation  │
│ - 5,000+ race runs      │
│ - Add noise/chaos       │
│ - Calculate positions   │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────┐
│ calibration.py      │
│ Platt Scaling       │
│ - Adjust probabilities│
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Return to UI       │
│  - Display table    │
│  - Show charts      │
│  - Enable download  │
└─────────────────────┘
```

### 2. Live Data Flow (FastF1)

```
User Action: Select race + session
         │
         ▼
┌─────────────────────┐
│   live_data.py      │
│ - Parse selections  │
└────────┬────────────┘
         │
         ▼
┌──────────────────────────┐
│ fastf1_integration.py    │
│ get_session_data()       │
│                          │
│ Check cache first →      │
│   If cached: return      │
│   If not: fetch from API │
└────────┬─────────────────┘
         │
         ▼
┌─────────────────────┐
│   FastF1 Library    │
│ - Load session      │
│ - Fetch telemetry   │
│ - Get weather       │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ Cache in .fastf1_   │
│ cache directory     │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ Process with Pandas │
│ - Filter laps       │
│ - Convert times     │
│ - Calculate stats   │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ Visualize with      │
│ Plotly charts       │
│ - Line charts       │
│ - Bar charts        │
│ - Scatter plots     │
└─────────────────────┘
```

### 3. Driver Comparison Flow

```
User Action: Select 2 drivers + race
         │
         ▼
┌─────────────────────┐
│ comparisons.py      │
│ - Validate drivers  │
└────────┬────────────┘
         │
         ▼
┌──────────────────────────┐
│ fastf1_integration.py    │
│ compare_drivers_teardown │
│                          │
│ For each driver:         │
│   - Get fastest lap      │
│   - Extract telemetry    │
└────────┬─────────────────┘
         │
         ├──────────────────┐
         │                  │
         ▼                  ▼
┌─────────────────┐ ┌────────────────────┐
│  Driver 1 Tel   │ │  Driver 2 Tel      │
│ - Speed trace   │ │ - Speed trace      │
│ - Throttle      │ │ - Throttle         │
│ - Brake         │ │ - Brake            │
│ - RPM           │ │ - RPM              │
│ - Gear          │ │ - Gear             │
└────────┬────────┘ └────────┬───────────┘
         │                   │
         └────────┬──────────┘
                  │
                  ▼
┌─────────────────────────┐
│ Overlay on same chart   │
│ - Different colors      │
│ - Synchronized x-axis   │
│ - Interactive hover     │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────┐
│ Display time gap    │
│ Calculate delta     │
│ Show winner         │
└─────────────────────┘
```

---

## Caching Architecture

```
┌─────────────────────────────────────────────────┐
│              Caching Layers                      │
└─────────────────────────────────────────────────┘

Layer 1: FastF1 Cache (.fastf1_cache/)
├── Session data (P1/P2/P3/Q/R)
├── Telemetry data
├── Weather data
├── Lap times
└── TTL: Persistent until manually cleared

Layer 2: Streamlit Cache (@st.cache_data)
├── get_season_schedule() - TTL: 1 hour
├── get_session_data() - TTL: 1 hour
├── get_lap_times() - TTL: 1 hour
├── get_fastest_laps() - TTL: 1 hour
├── get_driver_info() - TTL: 24 hours
└── get_race_results() - TTL: 1 hour

Layer 3: Session State (st.session_state)
├── User selections
├── Loaded datasets
├── Intermediate calculations
└── TTL: Until page refresh

Cache Hit Flow:
User Request → Check Streamlit Cache → Return cached result

Cache Miss Flow:
User Request → Check FastF1 Cache → Fetch from API → 
Store in both caches → Return result
```

---

## Module Dependencies

```
streamlit_app.py
├── pages/
│   ├── predictions.py
│   │   ├── engine/predictor.py
│   │   ├── data/circuit_data.py
│   │   └── fastf1_integration.py
│   │
│   ├── live_data.py
│   │   └── fastf1_integration.py
│   │       └── FastF1 library
│   │
│   ├── driver_analytics.py
│   │   └── fastf1_integration.py
│   │
│   ├── circuit_analysis.py
│   │   ├── fastf1_integration.py
│   │   └── data/circuit_data.py
│   │
│   └── comparisons.py
│       └── fastf1_integration.py
│
└── fastf1_integration.py
    ├── FastF1 library
    ├── pandas
    ├── numpy
    └── matplotlib
```

---

## Technology Stack

```
Frontend Layer:
├── Streamlit 1.31+
│   ├── Multi-page navigation
│   ├── Interactive widgets
│   ├── Session state management
│   └── Custom theming
│
└── Plotly 5.18+
    ├── Line charts
    ├── Bar charts
    ├── Scatter plots
    ├── Radar charts
    └── Interactive features

Data Layer:
├── FastF1 3.1+
│   ├── Session loading
│   ├── Telemetry extraction
│   ├── Lap time analysis
│   └── Weather data
│
├── Pandas 2.2+
│   ├── Data manipulation
│   ├── Time series handling
│   └── Statistical operations
│
└── NumPy 1.26+
    ├── Numerical computations
    └── Array operations

Prediction Engine:
├── Monte Carlo simulation
├── Platt calibration
├── Feature engineering
└── Probability modeling

Infrastructure:
├── Python 3.10+
├── Virtual environment
├── Dependency management
└── Caching system
```

---

## Security Model

```
┌────────────────────────────────────────┐
│         Security Considerations        │
└────────────────────────────────────────┘

Local Deployment (Default):
✓ Runs on localhost only
✓ No external access
✓ No authentication needed
✓ Firewall protects by default

Public Deployment (Streamlit Cloud):
✓ HTTPS enabled automatically
✓ Isolated container environment
✓ No sensitive data exposed
⚠ App is publicly accessible
⚠ Add auth if needed (Enterprise)

Self-Hosted (VPS/Docker):
✓ Can add nginx reverse proxy
✓ Can implement authentication
✓ Can set up rate limiting
✓ Full control over security
⚠ Must configure manually
⚠ Regular updates required

Data Privacy:
✓ No personal data collected
✓ No user accounts
✓ No database storage
✓ All processing in-memory
✓ Cache contains public F1 data only
```

---

## Performance Characteristics

```
Operation                  | Time (typical)    | Cache Impact
---------------------------|-------------------|-------------
App startup                | 2-5 seconds       | First load only
Page navigation            | < 1 second        | Instant after first
Load season schedule       | 1-3 seconds       | Cached 1 hour
Load session data          | 5-30 seconds      | Cached persistently
Fetch telemetry            | 2-10 seconds      | Cached persistently
Run prediction (5K sims)   | 5-15 seconds      | Not cached
Generate charts            | 1-3 seconds       | Re-rendered each view
Export CSV                 | < 1 second        | On-demand

Optimization Strategies:
1. Aggressive caching reduces repeated loads
2. Lazy loading defers expensive operations
3. Sampling limits data for historical analysis
4. Session state preserves intermediate results
5. Parallel loading where possible
```

---

## Scalability Analysis

```
Current Design:
- Single-user focus
- In-memory processing
- Local file caching
- Suitable for: 1-10 concurrent users

Scaling to 100+ Users:
✓ Use Streamlit Cloud (auto-scales)
✓ Add Redis cache layer
✓ Implement request queuing
✓ Use CDN for static assets
✓ Database for persistent storage

Scaling to 1000+ Users:
✓ Deploy on Kubernetes
✓ Add load balancer
✓ Implement microservices
✓ Use message queue (RabbitMQ)
✓ Horizontal pod scaling

Bottlenecks to Watch:
1. FastF1 API rate limits
2. Memory usage for large datasets
3. CPU for Monte Carlo simulations
4. Network bandwidth for telemetry
5. Disk I/O for cache operations
```

---

This architecture provides a solid foundation for an interactive F1 analytics platform that is both powerful and maintainable.
