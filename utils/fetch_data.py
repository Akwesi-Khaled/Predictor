import requests
import json
import os
import time
from datetime import date


BASE_URL = "https://api.football-data.org/v4/"
CACHE_DIR = "cache"
CACHE_EXPIRY_HOURS = 4 # refresh every 6 hours


if not os.path.exists(CACHE_DIR):
os.makedirs(CACHE_DIR)


headers = lambda api_key: {"X-Auth-Token": api_key}


def cache_data(filename, data):
record = {"timestamp": time.time(), "data": data}
with open(os.path.join(CACHE_DIR, filename), 'w') as f:
json.dump(record, f)


def load_cache(filename):
path = os.path.join(CACHE_DIR, filename)
if os.path.exists(path):
with open(path, 'r') as f:
record = json.load(f)
age_hours = (time.time() - record['timestamp']) / 3600
if age_hours < CACHE_EXPIRY_HOURS:
return record['data']
return None


def get_leagues(api_key):
cache_file = "leagues.json"
cached = load_cache(cache_file)
if cached:
return cached


resp = requests.get(BASE_URL + "competitions", headers=headers(api_key))
if resp.status_code == 200:
data = resp.json()
leagues = [c['name'] for c in data['competitions'] if c['plan'] == 'TIER_ONE']
cache_data(cache_file, leagues)
return leagues
elif cached:
return cached
return []


def get_fixtures(api_key, fixture_date, league_name):
cache_file = f"fixtures_{fixture_date}_{league_name}.json".replace(' ', '_')
cached = load_cache(cache_file)
if cached:
return cached


params = {'dateFrom': fixture_date.isoformat(), 'dateTo': fixture_date.isoformat()}
resp = requests.get(BASE_URL + "matches", headers=headers(api_key), params=params)
if resp.status_code == 200:
data = resp.json().get('matches', [])
league_matches = [m for m in data if m['competition']['name'] == league_name]
cache_data(cache_file, league_matches)
return []
