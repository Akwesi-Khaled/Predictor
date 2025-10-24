# utils/api_sports.py
import requests
import json
import os
import time
from typing import Any, Dict, List, Optional

BASE = "https://v3.football.api-sports.io"
CACHE_DIR = "cache_api_sports"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def _cache_path(name: str) -> str:
    safe = name.replace("/", "_").replace(" ", "_")
    return os.path.join(CACHE_DIR, f"{safe}.json")

def _save_cache(name: str, data: Any):
    path = _cache_path(name)
    with open(path, "w", encoding="utf-8") as f:
        record = {"ts": time.time(), "data": data}
        json.dump(record, f)

def _load_cache(name: str, max_age_seconds: int = 3600) -> Optional[Any]:
    path = _cache_path(name)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            record = json.load(f)
        age = time.time() - float(record.get("ts", 0))
        if age <= max_age_seconds:
            return record.get("data")
    except Exception:
        return None
    return None

class APISportsClient:
    def __init__(self, api_key: str):
        self.key = api_key
        self.headers = {
            "x-apisports-key": api_key
        }

    def _get(self, path: str, params: Dict = None, cache_name: str = None, cache_ttl: int = 3600):
        url = BASE.rstrip("/") + path
        try:
            r = requests.get(url, headers=self.headers, params=params, timeout=15)
            r.raise_for_status()
            data = r.json()
            if cache_name:
                _save_cache(cache_name, data)
            return data
        except Exception as e:
            # fallback to cache if available
            if cache_name:
                cached = _load_cache(cache_name, max_age_seconds=cache_ttl)
                if cached is not None:
                    return cached
            # re-raise so caller can handle or show error
            raise

    # Leagues (competitions) - we will return list of {id, name, country}
    def get_leagues(self, season: int = None):
        params = {}
        if season:
            params["season"] = season
        return self._get("/leagues", params=params, cache_name="leagues", cache_ttl=24*3600)

    # Fixtures by date
    def get_fixtures_by_date(self, date_iso: str, league_id: int = None):
        params = {"date": date_iso}
        if league_id:
            params["league"] = league_id
        return self._get("/fixtures", params=params, cache_name=f"fixtures_{date_iso}_{league_id or 'all'}")

    # Predictions for a fixture
    def get_predictions(self, fixture_id: int):
        return self._get("/predictions", params={"fixture": fixture_id}, cache_name=f"pred_{fixture_id}", cache_ttl=3600)

    # Standings for a league and season
    def get_standings(self, league_id: int, season: int):
        return self._get("/standings", params={"league": league_id, "season": season}, cache_name=f"standings_{league_id}_{season}", cache_ttl=3600)

    # Team statistics (xG etc.) for team in league/season
    def get_team_stats(self, team_id: int, league_id: int = None, season: int = None):
        params = {"team": team_id}
        if league_id:
            params["league"] = league_id
        if season:
            params["season"] = season
        return self._get("/teams/statistics", params=params, cache_name=f"teamstats_{team_id}_{league_id}_{season}", cache_ttl=3600)

    # Lineups for a fixture
    def get_lineups(self, fixture_id: int):
        return self._get("/fixtures/lineups", params={"fixture": fixture_id}, cache_name=f"lineup_{fixture_id}", cache_ttl=3600)

    # Historical matches for a team (season)
    def get_team_fixtures(self, team_id: int, season: int = None, status: str = None):
        params = {"team": team_id}
        if season:
            params["season"] = season
        if status:
            params["status"] = status
        return self._get("/fixtures", params=params, cache_name=f"teamfixtures_{team_id}_{season}_{status}", cache_ttl=6*3600)
