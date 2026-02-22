# 🇦🇷 Argentina Football Analytics Dashboard

**DSA 506: Visual Analytics and Communications — Spring 2026**  
**SUNY Polytechnic Institute**

A Streamlit-powered interactive dashboard analyzing Argentina's international football performance from 1902 to 2025.

---

## 📊 Dashboard Overview

**Analytical Objective:** Track Argentina's long-term international football performance across tournaments, examine goal-scoring patterns, evaluate head-to-head records against top rivals, and assess performance in high-pressure penalty shootouts.

**Live App:** [Click here to open the dashboard](#) *(replace with your Streamlit Cloud URL)*

---

## 📁 Repository Structure

```
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
├── results.csv             # Match results (1872–2025)
├── goalscorers.csv         # Individual goal scorer data
├── shootouts.csv           # Penalty shootout outcomes
├── former_names.csv        # Country name changes over time
└── README.md               # This file
```

---

## 📂 Data Provenance

### Source
All data comes from the publicly available Kaggle dataset:

**"International Football Results from 1872 to 2025"**  
URL: https://www.kaggle.com/datasets/martj42/international-football-results-from-1872-to-2017  
License: Open Data / Public Domain  
Collected by: Mart Jürisoo

### Files and Contents

| File | Description |
|------|-------------|
| `results.csv` | Match-level results: date, home team, away team, scores, tournament, city, country, neutral venue flag |
| `goalscorers.csv` | Goal-level data: date, teams, scorer name, minute, own goal flag, penalty flag |
| `shootouts.csv` | Penalty shootout outcomes: date, teams, winner, first shooter |
| `former_names.csv` | Historical country name mappings (e.g., Zaire → DR Congo) |

### Collection Method
Data was downloaded directly as CSV files from Kaggle. No API or scraping was used.  
Steps to download:
1. Create a free Kaggle account at https://www.kaggle.com
2. Navigate to the dataset URL above
3. Click **Download** to get the zip archive
4. Extract all four CSV files into the root of this repository

---

## 🔄 Data Update Procedure

When a new international match window or tournament concludes:

1. Return to the Kaggle dataset page and check for an updated version (the dataset maintainer updates it regularly after major tournaments).
2. Download the new CSV archive.
3. Replace `results.csv`, `goalscorers.csv`, and `shootouts.csv` in the repository with the new versions.
4. Commit and push to GitHub — Streamlit Community Cloud will automatically redeploy with the new data.

If the Kaggle dataset is no longer maintained, the same data can be sourced from:
- **football-data.co.uk** — https://www.football-data.co.uk/
- **OpenFootball GitHub** — https://github.com/openfootball/south-america
- **API alternative:** [football-data.org API](https://www.football-data.org/) (free tier available, provides match results via REST API)

---

## 🚀 Running Locally

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/argentina-football-dashboard.git
cd argentina-football-dashboard

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
streamlit run app.py
```

The app will open at `http://localhost:8501`

---

## ☁️ Deploying to Streamlit Community Cloud

1. Push this repository to GitHub (make it **public**)
2. Go to https://share.streamlit.io and sign in with GitHub
3. Click **New app** → select this repo → set main file to `app.py`
4. Click **Deploy** — the app will be live within a few minutes

---

## 📈 Dashboard Features

- **4 Chart Types:** Bar charts, line charts, scatter plots, pie/donut charts
- **3 Tabs:** Overall Performance | Goals & Scorers | Tournaments & Rivals
- **Interactive Filters:** Year range slider, tournament multiselect (sidebar)
- **KPI Metric Cards:** Total matches, wins, draws, losses, win rate, goals scored
- **Written Interpretations:** Each visualization includes a humanized analytical interpretation embedded directly in the dashboard

---

## 👤 Author

Mayank Waghmare  
MS Data Science — SUNY Polytechnic Institute  
DSA 506: Visual Analytics and Communications, Spring 2026
