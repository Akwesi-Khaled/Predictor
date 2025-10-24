# app.py
import streamlit as st
from datetime import date
from dateutil import parser
import pandas as pd
from utils.api_sports import APISportsClient
import math

st.set_page_config(page_title="Football Predictor (api-sports.io)", layout="wide")

st.title("⚽ Football Predictor — API-Football (api-sports.io)")
st.write("Shows fixtures and API-provided predictions. Uses caching + fallback.")

# load API key from Streamlit secrets
API_KEY = st.secrets.get("API_FOOTBALL_KEY")
if not API_KEY:
    st.error("API key not found. Add API_FOOTBALL_KEY to Streamlit secrets.")
    st.stop()

client = APISportsClient(API_KEY)

# Sidebar: selectors + filters
st.sidebar.header("Date & League")
selected_date = st.sidebar.date_input("Select date", value=date.today())
season_input = st.sidebar.number_input("Season (year)", min_value=2000, max_value=2100, value=date.today().year)
# We'll fetch leagues list (cached)
with st.sidebar.expander("League selector"):
    try:
        leagues_data = client.get_leagues(season=season_input)
        # leagues_data may have structure: {"response": [...]}
        leagues_resp = leagues_data.get("response", []) if isinstance(leagues_data, dict) else []
        choices = []
        for l in leagues_resp:
            # different versions return nested structures
            if isinstance(l, dict) and "league" in l:
                league_obj = l["league"]
                choices.append((league_obj.get("id"), f'{league_obj.get("name")} ({league_obj.get("country")})'))
            elif "name" in l and "id" in l:
                choices.append((l.get("id"), l.get("name")))
        if not choices:
            # fallback: try parsing when api returns list of competitions
            choices = [(c.get("id"), f'{c.get("name")} ({c.get("area", {}).get("name","")})') for c in leagues_data.get("response", [])]
        league_choice = st.selectbox("League (optional)", options=[None] + choices, format_func=lambda x: "All Leagues" if x is None else x[1])
        # user will get tuple or None
    except Exception as e:
        st.sidebar.error(f"Failed to load leagues: {e}")
        league_choice = None

# Filters
st.sidebar.header("Prediction Filters")
use_predictions = st.sidebar.checkbox("Show API Predictions (built-in)", True)
show_lineups = st.sidebar.checkbox("Show Lineups/Injuries", False)
show_team_stats = st.sidebar.checkbox("Show Team Stats (xG, possession)", False)
min_conf = st.sidebar.slider("Min confidence % to show", 0, 100, 35)

# Prepare league id (if selected)
league_id = None
league_label = "All Leagues"
if league_choice:
    if isinstance(league_choice, tuple):
        league_id = league_choice[0]
        league_label = league_choice[1]
    else:
        league_id = getattr(league_choice, "id", None)

# Fetch fixtures for date
date_iso = selected_date.isoformat()
try:
    fixtures_resp = client.get_fixtures_by_date(date_iso, league_id=league_id)
    fixtures = fixtures_resp.get("response", []) if isinstance(fixtures_resp, dict) else fixtures_resp
except Exception as e:
    st.error(f"Failed to fetch fixtures: {e}")
    fixtures = []

if not fixtures:
    st.info("No fixtures available for the selected date.")
else:
    st.subheader(f"Fixtures for {date_iso} — {league_label}")
    for f in fixtures:
        # parse fixture structure from api-sports
        fixture = f.get("fixture", {})
        teams = f.get("teams", {})
        league = f.get("league", {})
        fixture_id = fixture.get("id")
        kickoff_local = fixture.get("date")
        kickoff_time = kickoff_local[11:16] if kickoff_local else "TBD"
        home = teams.get("home", {}).get("name", "Home")
        away = teams.get("away", {}).get("name", "Away")
        row_title = f"**{home}** vs **{away}** — 🕒 {kickoff_time} ({league.get('name')})"
        st.markdown(row_title)

        # predictions (API)
        if use_predictions and fixture_id:
            try:
                pred_resp = client.get_predictions(fixture_id)
                pred_list = pred_resp.get("response", []) if isinstance(pred_resp, dict) else pred_resp
                if pred_list:
                    # the API may return multiple predictor sources; pick first
                    p = pred_list[0]
                    # p commonly contains 'predictions' with 'winner' and 'advice' and 'percent'
                    if "predictions" in p and isinstance(p["predictions"], list) and p["predictions"]:
                        block = p["predictions"][0]
                        winner = block.get("winner", {}).get("name") or block.get("winner")
                        advice = block.get("advice")
                        # probabilities
                        probs = {}
                        for key in ("home", "draw", "away"):
                            val = block.get("probability", {}).get(key)
                            if val is not None:
                                probs[key] = f"{val}%"
                        conf = None
                        # best available confidence: if 'probability' exists choose max
                        if probs:
                            # map to numeric
                            numeric = [int(str(v).replace("%","")) for v in probs.values() if isinstance(v, str) and v.strip("%").isdigit()]
                            if numeric:
                                conf = max(numeric)
                        # display
                        if conf is None:
                            st.caption(f"Prediction: {winner} — {advice if advice else ''}")
                        else:
                            if conf >= min_conf:
                                st.caption(f"🔮 Prediction: {winner} — Confidence {conf}% — {advice if advice else ''}")
                            else:
                                st.caption(f"🔮 Prediction available but confidence {conf}% < min threshold {min_conf}%")
                    else:
                        st.caption("No prediction data available for this fixture.")
                else:
                    st.caption("No prediction returned by API.")
            except Exception as e:
                st.caption(f"Prediction fetch error (using cache fallback if available): {e}")

        # lineups
        if show_lineups and fixture_id:
            try:
                lu = client.get_lineups(fixture_id)
                lu_resp = lu.get("response", []) if isinstance(lu, dict) else lu
                # show brief names for each team if present
                for team_block in lu_resp:
                    team_name = team_block.get("team", {}).get("name")
                    formation = team_block.get("formation")
                    starters = team_block.get("startXI", [])
                    st.write(f"- {team_name}: formation {formation}, starters {len(starters)}")
            except Exception as e:
                st.write(f"- Lineup fetch error: {e}")

        # optional team stats (xG)
        if show_team_stats:
            try:
                home_id = teams.get("home", {}).get("id")
                away_id = teams.get("away", {}).get("id")
                # fetch team stats (league + season useful but optional)
                if home_id:
                    hs = client.get_team_stats(home_id, league_id, season_input)
                    st.write("Home team stats:", hs.get("response", {}))
                if away_id:
                    as_ = client.get_team_stats(away_id, league_id, season_input)
                    st.write("Away team stats:", as_.get("response", {}))
            except Exception as e:
                st.write(f"- Team stats fetch error: {e}")

        st.divider()
