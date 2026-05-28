# 🏎️ F1 Predictions & Analytics - Streamlit Dashboard

An interactive web application for Formula 1 race predictions, live data analysis, and driver performance insights. Built with **Streamlit** and powered by **FastF1**.

## ✨ Features

### 🏁 Race Predictions
- **Probabilistic predictions** using Monte Carlo simulations (5,000+ runs)
- Interactive controls for rain probability, simulation count, and grid overrides
- Beautiful visualizations of win/podium/DNF probabilities
- Downloadable prediction results

### 📊 Live Race Data (FastF1 Integration)
- **Real-time lap times** from any F1 session (Practice, Qualifying, Race)
- **Telemetry visualization**: Speed, throttle, brake, RPM, gear data
- **Weather conditions** throughout sessions
- Fastest lap comparisons with gap analysis
- Sector time breakdowns

### 👤 Driver Analytics
- Season performance tracking with points progression
- Historical race results across multiple seasons
- **Teammate head-to-head comparisons**
- Qualifying vs race performance analysis
- Career statistics and trends

### 🏎️ Circuit Analysis
- Track characteristics and profiles
- Historical winners at each circuit
- Team dominance patterns
- Lap time analysis by driver

### ⚖️ Comparisons
- **Side-by-side driver comparisons** with telemetry overlays
- Season-long battle tracking
- Custom race/session selection
- Detailed performance metrics

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- Git (optional)

### Installation

1. **Clone or download the project**
   ```bash
   cd "c:\Users\PC\Music\F1MLpredictions2 -streamlit"
   ```

2. **Create and activate virtual environment**
   ```bash
   # Windows
   py -m venv .venv
   .venv\Scripts\activate
   
   # Mac/Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Streamlit app**
   ```bash
   streamlit run streamlit_app.py
   ```

5. **Open your browser**
   The app will automatically open at `http://localhost:8501`

## 📱 Using the App

### Navigation
The app has 5 main pages accessible via the sidebar:

1. **🏁 Race Predictions** - Run probabilistic race outcome predictions
2. **📊 Live Race Data** - Explore real F1 data with FastF1
3. **👤 Driver Analytics** - Deep dive into driver performance
4. **🏎️ Circuit Analysis** - Track characteristics and history
5. **⚖️ Comparisons** - Head-to-head driver battles

### Tips for Best Experience

- **First load may be slow**: FastF1 downloads and caches race data. Subsequent loads are much faster.
- **Use filters**: Select specific drivers, races, and sessions to focus your analysis.
- **Download data**: Most tables can be exported as CSV for further analysis.
- **Explore telemetry**: The telemetry comparison tool shows incredible detail about driving styles.

## 🔧 Configuration

### FastF1 Cache
The app automatically caches FastF1 data in `.fastf1_cache` directory. This speeds up subsequent loads significantly.

To clear cache:
```bash
rm -rf .fastf1_cache  # Mac/Linux
rmdir /s .fastf1_cache  # Windows
```

### Streamlit Settings
Create `.streamlit/config.toml` for custom settings:

```toml
[server]
port = 8501
headless = true

[theme]
primaryColor = "#FF1801"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
```

## 📊 Data Sources

- **FastF1 API**: Real-time F1 data including lap times, telemetry, weather
- **Internal Prediction Engine**: Custom Monte Carlo simulation model
- **Historical Database**: 2024-2026 season data

## 🎨 Visualizations

The app uses **Plotly** for interactive charts:
- Hover over data points for details
- Zoom and pan on charts
- Toggle traces on/off
- Download charts as PNG

## 🏗️ Project Structure

```
F1MLpredictions2-streamlit/
├── streamlit_app.py          # Main app entry point
├── fastf1_integration.py     # FastF1 data fetching module
├── pages/                    # Multi-page navigation
│   ├── predictions.py        # Race predictions page
│   ├── live_data.py          # Live race data page
│   ├── driver_analytics.py   # Driver performance page
│   ├── circuit_analysis.py   # Circuit info page
│   └── comparisons.py        # Driver comparison page
├── engine/                   # Existing prediction engine
├── data/                     # F1 data files
├── config/                   # Configuration
└── requirements.txt          # Python dependencies
```

## 🔍 Key Technologies

- **Streamlit**: Web UI framework
- **FastF1**: F1 data access library
- **Plotly**: Interactive visualizations
- **Pandas**: Data manipulation
- **Existing ML Engine**: Probabilistic predictions

## 💡 Example Use Cases

### For F1 Fans
- Check predictions before watching races
- Compare your favorite drivers' performance
- Understand why certain drivers excel at specific tracks

### For Data Analysts
- Export lap time data for custom analysis
- Study telemetry patterns
- Analyze team strategies

### For Content Creators
- Generate charts for videos/articles
- Find interesting storylines (teammate battles, etc.)
- Track driver development over time

## ⚠️ Important Notes

1. **Data Availability**: Not all historical sessions may be available immediately after races. FastF1 updates data periodically.

2. **Internet Required**: The app needs internet access to fetch data from FastF1 APIs.

3. **Cache Size**: FastF1 cache can grow large (several GB). Clean it occasionally.

4. **Performance**: Loading telemetry data is computationally intensive. Be patient on first load.

## 🐛 Troubleshooting

### "Module not found" errors
```bash
pip install -r requirements.txt
```

### Slow loading
- Enable FastF1 cache (automatic)
- Select fewer races/drivers
- Use recent seasons (more data available)

### Charts not displaying
- Ensure you have Plotly installed: `pip install plotly`
- Try refreshing the browser
- Check browser console for errors

### FastF1 connection errors
- Check your internet connection
- FastF1 servers may be temporarily unavailable
- Retry after a few minutes

## 📈 Future Enhancements

Planned features:
- [ ] Live race tracking during weekends
- [ ] Betting odds integration
- [ ] Fantasy F1 recommendations
- [ ] Driver career mode (all-time stats)
- [ ] Team radio analysis
- [ ] Tire strategy optimizer
- [ ] Weather impact predictions

## 🤝 Contributing

Contributions welcome! Areas of interest:
- Additional visualization types
- More sophisticated prediction models
- UI/UX improvements
- Documentation enhancements

## 📄 License

This project maintains the same license as the original F1MLpredictions2 project.

## 🙏 Acknowledgments

- **FastF1**: Incredible library for F1 data access
- **Streamlit**: Amazing framework for data apps
- **Original F1MLpredictions2**: Foundation for prediction engine
- **Formula 1**: For the exciting sport we all love

---

**Built with ❤️ for F1 fans everywhere**

*Version 2.0 - Streamlit Edition*
