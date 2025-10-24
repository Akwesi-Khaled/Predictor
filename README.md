# ⚽ Football Predictor Web App (Football-Data.org + Auto Cache Expiry)


A web app that fetches fixtures from [football-data.org](https://www.football-data.org/) and displays predictions based on advanced filters.


### 🌐 Features
- Fetch live fixtures and predictions
- League selector + Date range picker
- 8 prediction filters (home, form, goals, head-to-head, ML, injuries, standings, xG)
- **Automatic caching with 4-hour expiry**


### ⚙️ Setup
1. Clone this repo
2. Add your API key in Streamlit Cloud → Secrets:
```toml
FOOTBALL_DATA_API = "your_football_data_org_api_key"
