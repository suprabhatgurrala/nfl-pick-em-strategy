import requests
import pandas as pd

BASE_URL = "https://guest.api.arcadia.pinnacle.com/0.1/leagues/889"


def map_id_to_odds(matchup_id, odds_dict):
    """
    Helper method to get the odds for a given matchup ID from the odds dict.
    """
    odds = odds_dict.get(matchup_id)
    if odds:
        return pd.Series(odds)


def get_vegas_data():
    """
    Pulls moneylines from Pinnacle
    """
    matchups_response = requests.get(f"{BASE_URL}/matchups")
    matchups_response.raise_for_status()
    matchups_data = matchups_response.json()

    odds_response = requests.get(f"{BASE_URL}/markets/straight")
    odds_response.raise_for_status()
    odds_data = odds_response.json()

    matchups_list = []
    for i in matchups_data:
        if i.get("type") == "matchup" and i.get("parent") is None:
            matchup_id = i["id"]
            for participant in i.get("participants", []):
                if participant["alignment"] == "home":
                    home_team = participant["name"]
                elif participant["alignment"] == "away":
                    away_team = participant["name"]
            matchups_list.append(
                {
                    "id": matchup_id,
                    "away": away_team,
                    "home": home_team,
                    "status": i["status"],
                    "startTime": i["startTime"],
                }
            )

    # Odds are not available in /matchups endpoint
    # Create a dict to map matchupId to odds
    odds_dict = {}
    for i in odds_data:
        if i.get("type") == "moneyline" and i.get("period") == 0:
            matchup_id = i["matchupId"]
            home_ml = None
            away_ml = None
            for price_data in i.get("prices", []):
                if price_data.get("designation") == "home":
                    home_ml = price_data["price"]
                elif price_data.get("designation") == "away":
                    away_ml = price_data["price"]
            if home_ml or away_ml:
                odds_dict[matchup_id] = {
                    "away_ml": away_ml,
                    "home_ml": home_ml,
                }

    df = pd.DataFrame(matchups_list)
    df[["home_ml", "away_ml"]] = df.apply(
        lambda x: map_id_to_odds(x.id, odds_dict), axis=1
    )
    return df.sort_values(["startTime", "id"])


if __name__ == "__main__":
    print(get_vegas_data())
