import streamlit as st
import requests
from datetime import date
from functools import lru_cache

# -----------------------------------------------------------
# ⚙️ CONFIGURATION
# -----------------------------------------------------------
st.set_page_config(page_title="Football Predictions", page_icon="⚽", layout="wide")
st.title("⚽ Football Match Predictions")
st.caption("Powered by API-Football | Built with Streamlit")

API_KEY = st.secrets["API_FOOTBALL_KEY"]
API_BASE = "https://v3.football.api-sports.io"

HEADERS = {"x-apisports-key": API_KEY}

# -----------------------------------------------------------
# 🧠 BASIC CACHING SYSTEM (with expiry)
# -----------------------------------------------------------
@st.cache_data(ttl=3600)  # cache for 1 hour
def fetch_data(endpoint, params=None):
    """Fetch data from API-Football with basic caching & error handling."""
    try:
        response = requests.get(f"{API_BASE}/{endpoint}", headers=HEADERS, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"API Error: {e}")
        return {}

# -----------------------------------------------------------
# 🎚️ USER CONTROLS
# -----------------------------------------------------------
st.sidebar.header("⚙️ Settings")

season_input = st.sidebar.selectbox("Select Season", options=[2025, 2024, 2023, 2022], index=0)
selected_date = st.sidebar.date_input("Select Match Date", value=date.today())

# -----------------------------------------------------------
# 🏆 LEAGUE SELECTOR — Top 20 Major Leagues
# -----------------------------------------------------------
st.sidebar.header("🏆 League Selector")

TOP_LEAGUES = [
    "Premier League", "Championship", "La Liga", "Serie A", "Bundesliga",
    "Ligue 1", "Eredivisie", "Primeira Liga", "Scottish Premiership", "MLS",
    "Brasileirão Serie A", "Argentine Liga Profesional", "Saudi Pro League",
    "UEFA Champions League", "UEFA Europa League", "Turkish Super Lig",
    "Belgian Pro League", "Swiss Super League", "Russian Premier League", "A-League"
]

league_id, league_label = None, None

try:
    leagues_data = fetch_data("leagues", params={"season": season_input})
    leagues_resp = leagues_data.get("response", []) if isinstance(leagues_data, dict) else []

    league_options = []
    for l in leagues_resp:
        if not isinstance(l, dict) or "league" not in l:
            continue
        league_obj = l["league"]
        country_obj = l.get("country", {})
        league_name = league_obj.get("name", "")
        country_name = country_obj.get("name", "")
        league_id_val = league_obj.get("id")

        if league_name in TOP_LEAGUES and league_id_val:
            label = f"{country_name} — {league_name}"
            league_options.append((league_id_val, label))

    if not league_options:
        st.sidebar.warning("⚠️ No top leagues found for this season.")
        st.stop()

    league_options = sorted(league_options, key=lambda x: x[1])

    league_choice = st.sidebar.selectbox(
        "Select a League",
        options=league_options,
        format_func=lambda x: x[1]
    )

    if league_choice:
        league_id = league_choice[0]
        league_label = league_choice[1]

except Exception as e:
    st.sidebar.error(f"Failed to load leagues: {e}")
    st.stop()

# -----------------------------------------------------------
# ⚽ FIXTURES + PREDICTIONS
# -----------------------------------------------------------
if league_id and league_label:
    st.subheader(f"⚽ Fixtures for {league_label} — {selected_date}")

    fixtures = []
    try:
        fixtures_data = fetch_data("fixtures", params={"league": league_id, "season": season_input, "date": selected_date})
        fixtures = fixtures_data.get("response", []) if isinstance(fixtures_data, dict) else []

        if not fixtures:
            st.warning("No fixtures available for the selected date.")
        else:
            for fixture in fixtures:
                fixture_info = fixture.get("fixture", {})
                teams = fixture.get("teams", {})
                home = teams.get("home", {}).get("name", "Home Team")
                away = teams.get("away", {}).get("name", "Away Team")
                fixture_id = fixture_info.get("id")

                st.markdown(f"### {home} 🆚 {away}")

                # 🧩 Fetch prediction for the fixture
                prediction_data = fetch_data("predictions", params={"fixture": fixture_id})
                prediction = prediction_data.get("response", [])
                if prediction:
                    pred = prediction[0]
                    advice = pred.get("advice", "No prediction available")
                    st.info(f"**Prediction:** {advice}")
                else:
                    st.write("No prediction data available.")
    except Exception as e:
        st.error(f"Error fetching fixtures: {e}")
else:
    st.info("Please select a league from the sidebar to view fixtures.")
