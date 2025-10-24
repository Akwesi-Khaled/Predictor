import random


class Predictor:
def __init__(self, home_adv, recent_form, goals_model, head_to_head, ml_model, injury_lineup, league_standing, xg_model):
self.home_adv = home_adv
self.recent_form = recent_form
self.goals_model = goals_model
self.head_to_head = head_to_head
self.ml_model = ml_model
self.injury_lineup = injury_lineup
self.league_standing = league_standing
self.xg_model = xg_model


def predict(self, home, away, previous_matches):
confidence = 50
prediction = "Draw"


if self.home_adv and len(home) % 2 == 0:
prediction = "Home Win"
confidence += 10
if self.recent_form:
confidence += random.randint(5, 10)
if self.goals_model:
confidence += random.randint(3, 8)
if self.head_to_head and home[0] < away[0]:
prediction = "Away Win"
confidence += 5
if self.ml_model:
confidence += random.randint(5, 10)
if self.injury_lineup:
confidence -= random.randint(0, 5)
if self.league_standing:
confidence += random.randint(5, 15)
if self.xg_model:
confidence += random.randint(5, 10)


return prediction, min(confidence, 99)
