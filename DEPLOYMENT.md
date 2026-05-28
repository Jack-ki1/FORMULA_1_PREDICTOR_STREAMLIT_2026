# Deploying the F1 Prediction System

A guide to hosting the F1 Prediction System as a web application.

---

## Architecture Overview

```
Python Prediction Engine
│
├── data/ + engine/        ← Python prediction system
│
└── scripts/generate_static_site.py
            │
            ▼
    Generates web/ (static HTML + JSON)
            │
            ▼
    Static web server serves web/
            │
            ▼
    https://your-domain.com/
```

The workflow generates a **fully static site** — no server required.
Chart.js is loaded from CDN. Predictions are pre-computed JSON files.

---

## Deployment Options

You can deploy the F1 Prediction System using one of the following methods depending on your needs.

### Option 1 — Static Site Hosting (Recommended)

This method generates a fully static site (HTML + JSON) that can be hosted anywhere (GitHub Pages, Netlify, Vercel, AWS S3, etc.). No server-side Python runtime is required for visitors.

1. **Generate the static site:**
   ```bash
   python scripts/generate_static_site.py
   ```
   *Optional parameters:*
   ```bash
   python scripts/generate_static_site.py --rain-probability 0.65 --simulations 10000
   ```

2. **Upload the `web/` directory:**
   Upload the contents of the generated `web/` folder to your hosting provider.

3. **Verify:**
   Open your domain to see the dashboard with predictions, standings, and charts.

#### Customising the Static Site
- **Branding:** Edit `<title>` and `<header>` in `scripts/generate_static_site.py`.
- **Custom Domain:** Configure your DNS and hosting provider settings as per their documentation.

---

### Option 2 — Streamlit Cloud

Deploy the interactive dashboard to Streamlit Cloud:

1. Create account at [streamlit.io/cloud](https://streamlit.io/cloud)
2. Connect your repository
3. Deploy!

---

### Option 3 — Self-Hosted Server

Run on your own server or VPS:

```bash
# Install dependencies
pip install -r requirements.txt

# Run Streamlit app
streamlit run app.py --server.port 8501 --server.address 0.0.0.0

# Or run API server
python app.py api --port 8000
```

Use nginx as a reverse proxy for production deployments.

---

## File Structure After Deployment

```
web/                            ← Published site root
├── index.html                  ← Main dashboard
├── predictions/
│   ├── canada.json
│   ├── monaco.json
│   └── ... (one per circuit)
└── assets/
    └── data.json               ← Full aggregate data for custom integrations
```

JSON files are publicly accessible at your domain:
```
https://your-domain.com/assets/data.json
https://your-domain.com/predictions/canada.json
```

This makes the system usable as a public API.

---

## Customizing Predictions

You can customize the generation process by modifying the script arguments or environment variables if supported by `generate_static_site.py`.

| Parameter | Description | Example |
|-----------|-------------|---------|
| `rain_probability` | Override rain chance | `0.65` for wet Monaco |
| `simulations` | Monte Carlo runs | `10000` for high precision |

Example usage (if supported by script):
```bash
python scripts/generate_static_site.py --rain-probability 0.65 --simulations 10000
```

---

## On-Demand Race Reports (PDF/HTML download)

The `predict.yml` workflow lets anyone with repo access generate a report:

1. Go to **Actions** → **"On-Demand Race Prediction"**
2. Click **"Run workflow"**
3. Enter circuit ID, rain probability, simulation count
4. After completion, download the HTML report from **Artifacts**

The artifact includes:
- `prediction_CIRCUIT.json` — raw prediction data
- `CIRCUIT_report.html` — styled standalone report

---

## Keeping the Deployed Site Fresh

For race weekends:

1. After qualifying (Saturday):
   ```bash
   # Update any grid position overrides if needed
   # Regenerate static site
   python scripts/generate_static_site.py
   # Upload web/ to your hosting provider
   ```

2. After the race (Sunday):
   ```bash
   python scripts/post_race_update.py --round 5 --circuit canada \
     --results "antonelli:1,russell:2,norris:3,..."
   # Regenerate and redeploy
   python scripts/generate_static_site.py
   ```

---

## Environment Variables

For optional features (weather API, live data sync), set environment variables:

| Variable | Description |
|-------------|-------------|
| `OPENWEATHER_API_KEY` | OpenWeatherMap API key for weather forecasts |
| `ERGAST_API_BASE` | Override default Ergast endpoint |

Set these in your deployment environment or `.env` file.

---

## Monitoring

Monitor your deployment based on your hosting provider:
- Check server logs for errors
- Set up uptime monitoring with services like UptimeRobot or Pingdom
- Monitor resource usage (CPU, memory) if self-hosting

---

## Monitoring & Alerts

Set up email notifications for failed deployments:
1. **Settings → Notifications → Actions**
2. Enable "Send notifications for failed workflows"

You'll get an email if the Thursday deploy fails (e.g. due to a Python error
after a data update).
