import streamlit as st
import pandas as pd
from datetime import date
from utils.fetch_data import get_fixtures, get_previous_matches, get_leagues
from utils.predict import Predictor

st.set_page_config(page_title="⚽ Football Predictor", layout="wide")

st.title("⚽ Football Prediction Web App")
st.write("Analyze fixtures, predict results, and explore league insights.")

# --- API Key ---
API_KEY = st.secrets["FOOTBALL_DATA_API"]

# --- Sidebar filters ---
st.sidebar.header("⚙️ Prediction Filters")
use_home_advantage = st.sidebar.checkbox("Home Advantage", True)
use_recent_form = st.sidebar.checkbox("Recent Form (Last 5 Games)", True)
use_goals_model = st.sidebar.checkbox("Goals Model", True)
use_head_to_head = st.sidebar.checkbox("Head-to-Head Stats", True)
use_machine_learning = st.sidebar.checkbox("ML Model", True)
use_injury_lineup = st.sidebar.checkbox("Injury/Lineup Influence", True)
use_league_standing = st.sidebar.checkbox("League Standing Influence", True)
use_xg_model = st.sidebar.checkbox("Expected Goals (xG) Model", True)
confidence_threshold = st.sidebar.slider("Minimum Confidence %", 50, 100, 60)

# --- Load Leagues ---
leagues = get_leagues(API_KEY)
selected_league = st.sidebar.selectbox("Select League", leagues)
selected_date = st.sidebar.date_input("Select Date", date.today())

# --- Load Fixtures & Past Matches ---
fixtures = get_fixtures(API_KEY, selected_date, selected_league)
previous_matches = get_previous_matches(API_KEY, selected_league)

# --- Initialize Predictor ---
predictor = Predictor(
    use_home_advantage,
    use_recent_form,
    use_goals_model,
    use_head_to_head,
    use_machine_learning,
    use_injury_lineup,
    use_league_standing,
    use_xg_model
)

# --- Display Predictions ---
if fixtures:
    st.subheader(f"🏆 {selected_league} — Fixtures for {selected_date}")
    for match in fixtures:
        home = match["homeTeam"]["name"]
        away = match["awayTeam"]["name"]
        time = match["utcDate"][11:16]

        prediction, confidence = predictor.predict(home, away, previous_matches)

        if confidence >= confidence_threshold:
            st.markdown(f"**{home} vs {away}** — 🕒 {time} UTC")
            st.caption(f"🔮 Prediction: {prediction} ({confidence:.1f}%)")
            st.divider()
else:
    st.info("No fixtures available for the selected date.")
