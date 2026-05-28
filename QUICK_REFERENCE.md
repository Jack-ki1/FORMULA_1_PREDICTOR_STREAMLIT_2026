# 📋 Quick Reference Guide

Common tasks and commands for the F1 Streamlit Dashboard.

---

## 🚀 Launching the App

### Windows
```bash
# Double-click this file:
RUN_STREAMLIT.bat

# Or manually:
.venv\Scripts\activate
streamlit run streamlit_app.py
```

### Mac/Linux
```bash
source .venv/bin/activate
streamlit run streamlit_app.py
```

**App opens at:** `http://localhost:8501`

---

## 🔧 Common Tasks

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Update Dependencies
```bash
pip install --upgrade streamlit fastf1 plotly
```

### Clear FastF1 Cache
```bash
# Windows
rmdir /s .fastf1_cache

# Mac/Linux
rm -rf .fastf1_cache
```

### Test Setup
```bash
python test_streamlit_setup.py
```

---

## 📊 Using the App

### Get Race Predictions
1. Go to **🏁 Race Predictions** page
2. Select circuit from dropdown
3. Adjust rain probability slider
4. Click **🚀 Run Prediction**
5. View results and download CSV

### View Live Lap Times
1. Go to **📊 Live Race Data** page
2. Select season and race
3. Choose session type (P1/Q/R)
4. Filter drivers to compare
5. Analyze lap time evolution

### Compare Driver Telemetry
1. Go to **⚖️ Comparisons** page
2. Select two drivers
3. Choose race and session
4. View speed/throttle/brake overlays
5. Analyze driving styles

### Check Driver Performance
1. Go to **👤 Driver Analytics** page
2. Select driver
3. View season progression
4. Compare with teammate
5. Export data as CSV

---

## 🎨 Customization

### Change Theme Colors
Edit `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#FF1801"        # F1 Red
backgroundColor = "#FFFFFF"      # White
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
```

### Change Default Port
Edit `.streamlit/config.toml`:
```toml
[server]
port = 8502
```

### Disable Usage Stats
Already configured in `.streamlit/config.toml`:
```toml
[browser]
gatherUsageStats = false
```

---

## 🐛 Troubleshooting

### App Won't Start
```bash
# Check Python version
python --version  # Need 3.10+

# Reinstall dependencies
pip install -r requirements.txt

# Test imports
python -c "import streamlit; import fastf1; import plotly"
```

### Slow Loading
- First load downloads FastF1 data (normal)
- Subsequent loads use cache (fast)
- Select fewer races/drivers
- Use recent seasons only

### Charts Not Showing
```bash
# Reinstall Plotly
pip install --upgrade plotly

# Clear browser cache
# Try different browser (Chrome/Firefox recommended)
```

### FastF1 Connection Error
- Check internet connection
- FastF1 APIs may be temporarily down
- Retry after few minutes
- App will work with limited functionality

### Memory Issues
```bash
# Clear caches
rm -rf .fastf1_cache
rm -rf .streamlit/cache

# Reduce simulation count in predictions
# Load fewer historical races
```

---

## 📱 Keyboard Shortcuts

When app is running:
- `R` - Rerun app
- `C` - Clear cache
- `Q` - Quit (in terminal)

---

## 🌐 Deployment Commands

### Streamlit Cloud
Push to GitHub, then connect at [streamlit.io/cloud](https://streamlit.io/cloud)

### Docker
```bash
docker build -t f1-dashboard .
docker run -p 8501:8501 f1-dashboard
```

### Heroku
```bash
heroku create your-app-name
# Deploy your code to Heroku following their documentation
heroku open
```

---

## 📈 Performance Tips

### For Faster Loading
```python
# In your code, limit data loading:
schedule = get_season_schedule(2026)  # Only current year
sample_races = schedule.head(5)       # Limit to 5 races
```

### For Better Responsiveness
- Use `@st.cache_data` for expensive operations
- Store large datasets in `st.session_state`
- Load telemetry only when requested

### For Production
- Enable HTTPS (automatic on Streamlit Cloud)
- Set up monitoring
- Regular cache cleanup
- Monitor resource usage

---

## 🔍 Debugging

### Enable Debug Mode
```bash
streamlit run streamlit_app.py --logger.level=debug
```

### View Logs
```bash
# Terminal shows real-time logs
# Check for errors in red text
```

### Check FastF1 Cache
```bash
ls -lh .fastf1_cache  # Mac/Linux
dir .fastf1_cache     # Windows
```

### Test Specific Page
Create test script:
```python
import streamlit as st
from pages.predictions import show

show()  # Test predictions page
```

---

## 📚 Useful Links

- **Streamlit Docs**: [docs.streamlit.io](https://docs.streamlit.io)
- **FastF1 Docs**: [docs.fastf1.dev](https://docs.fastf1.dev)
- **Plotly Gallery**: [plotly.com/python](https://plotly.com/python/)
- **F1 Calendar**: [formula1.com](https://www.formula1.com/en/racing/2026)

---

## 💬 Getting Help

### Before Asking for Help
1. ✅ Check this guide
2. ✅ Read error messages carefully
3. ✅ Search existing issues
4. ✅ Test with fresh virtual environment

### When Reporting Issues
Include:
- Python version
- Operating system
- Error message (full text)
- Steps to reproduce
- What you've tried

### Where to Ask
- GitHub Issues (bugs)
- GitHub Discussions (questions)
- Stack Overflow (general Python/Streamlit)

---

## 🎯 Quick Wins

### Want to impress friends?
1. Open app
2. Go to **Comparisons**
3. Select Verstappen vs teammate
4. Show telemetry overlay
5. Explain speed differences

### Want to predict next race?
1. Go to **Race Predictions**
2. Select upcoming circuit
3. Check weather forecast
4. Set rain probability
5. Run prediction
6. Share screenshot

### Want to analyze your favorite driver?
1. Go to **Driver Analytics**
2. Select driver
3. Scroll through season stats
4. Check teammate comparison
5. Download data for deeper analysis

---

## 🔄 Regular Maintenance

### Weekly
- Pull latest code updates
- Clear old FastF1 cache if large
- Check for dependency updates

### Monthly
- Review and update requirements
- Backup important data
- Test all pages work correctly

### Seasonally
- Add new season data
- Update circuit information
- Review prediction model accuracy

---

## 📞 Support Contacts

- **Project Issues**: GitHub Issues tab
- **Feature Requests**: GitHub Discussions
- **General Questions**: Stack Overflow (#streamlit, #fastf1)
- **F1 Data Questions**: FastF1 Discord/Forum

---

**Keep this guide handy for quick reference!** 🏎️💨
