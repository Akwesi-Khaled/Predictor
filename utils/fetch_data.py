import requests
import json
import os
import time
from datetime import date

BASE_URL = "https://api.football-data.org/v4/"
CACHE_DIR = "cache"
CACHE_EXPIRY_HOURS = 6  # refresh every 6 hours

# ✅ Ensure cache folder exists
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def headers(api_key):
    return {"X-Auth-Token": api_key}


# --- Cache Helpers ---
def cache_data(filename, data):
    record = {"timestamp": time.time(), "data": data}
    with open(os.path.join(CACHE_DIR, filename), "w") as f:
        json.dump(record, f)


def load_cache(filename):
    path = os.path.join(CACHE_DIR, filename)
    if os.path.exists(path):
        with open(path, "r") as f:
            record = json.load(f)
            age_hours = (time.time() - record["timestamp"]) / 3600
            if age_hours < CACHE_EXPIRY_HOURS:
                return record["data"]
    return None


# --- League Fetcher ---
def get_leagues(api_key):
    cache_file = "leagues.json"
    cached = load_cache(cache_file)
    if cached:
        return cached

    resp = requests.get(BASE_URL + "competitions", headers=headers(api_key))
    if resp.status_code == 200:
        data = resp.json()
        leagues = [c["name"] for c in data["competitions"] if c["plan"] == "TIER_ONE"]
        cache_data(cache_file, leagues)
        return leagues
    elif cached:
        return cached
    return []


# --- Fixtures Fetcher ---
def get_fixtures(api_key, fixture_date, league_name):
    cache_file = f"fixtures_{fixture_date}_{league_name}.json".replace(" ", "_")
    cached = load_cache(cache_file)
    if cached:
        return cached

    params = {"dateFrom": fixture_date.isoformat(), "dateTo": fixture_date.isoformat()}
    resp = requests.get(BASE_URL + "matches", headers=headers(api_key), params=params)
    if resp.status_code == 200:
        data = resp.json().get("matches", [])
        league_matches = [m for m in data if m["competition"]["name"] == league_name]
        cache_data(cache_file, league_matches)
        return league_matches
    elif cached:
        return cached
    return []


# --- Historical Matches Fetcher ---
def get_previous_matches(api_key, league_name):
    cache_file = f"previous_{league_name}.json".replace(" ", "_")
    cached = load_cache(cache_file)
    if cached:
        return cached

    resp = requests.get(BASE_URL + "competitions", headers=headers(api_key))
    if resp.status_code != 200 and cached:
        return cached

    comps = resp.json().get("competitions", [])
    comp = next((c for c in comps if c["name"] == league_name), None)
    if not comp:
        return cached if cached else []

    league_id = comp["id"]
    matches_resp = requests.get(
        BASE_URL + f"competitions/{league_id}/matches?status=FINISHED",
        headers=headers(api_key),
    )
    if matches_resp.status_code == 200:
        data = matches_resp.json().get("matches", [])
        cache_data(cache_file, data)
        return data
    elif cached:
        return cached
    return []
