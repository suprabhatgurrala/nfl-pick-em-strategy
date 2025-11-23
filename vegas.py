import requests
import pandas as pd

BASE_URL = "https://guest.api.arcadia.pinnacle.com/0.1/leagues/889"

vegas_name_to_abbrev = {
    # "Arizona Cardinals": "ARI",
    # "Atlanta Falcons": "ATL",
    # "Baltimore Ravens": "BAL",
    # "Buffalo Bills": "BUF",
    # "Carolina Panthers": "CAR",
    # "Chicago Bears": "CHI",
    # "Cincinnati Bengals": "CIN",
    # "Cleveland Browns": "CLE",
    # "Dallas Cowboys": "DAL",
    # "Denver Broncos": "DEN",
    # "Detroit Lions": "DET",
    # "Green Bay Packers": "GB",
    # "Houston Texans": "HOU",
    # "Indianapolis Colts": "IND",
    # "Jacksonville Jaguars": "JAC",
    # "Kansas City Chiefs": "KC",
    # "Las Vegas Raiders": "LV",
    # "Los Angeles Chargers": "LAC",
    # "Los Angeles Rams": "LAR",
    # "Miami Dolphins": "MIA",
    # "Minnesota Vikings": "MIN",
    # "New England Patriots": "NE",
    # "New Orleans Saints": "NO",
    # "New York Giants": "NYG",
    # "New York Jets": "NYJ",
    # "Philadelphia Eagles": "PHI",
    # "Pittsburgh Steelers": "PIT",
    # "San Francisco 49ers": "SF",
    # "Seattle Seahawks": "SEA",
    # "Tampa Bay Buccaneers": "TB",
    # "Tennessee Titans": "TEN",
    # "Washington Commanders": "WAS"
}


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
                    "Pinnacle ID": matchup_id,
                    "Away": away_team,
                    "Home": home_team,
                    "Status": i["status"],
                    "Start Time": i["startTime"],
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
                    "Pinnacle Away ML": away_ml,
                    "Pinnacle Home ML": home_ml,
                }

    df = pd.DataFrame(matchups_list)
    df[["Pinnacle Away ML", "Pinnacle Home ML"]] = df.apply(
        lambda x: map_id_to_odds(x["Pinnacle ID"], odds_dict), axis=1
    )
    return df.sort_values(["Start Time", "Pinnacle ID"])


if __name__ == "__main__":
    print(get_vegas_data())
