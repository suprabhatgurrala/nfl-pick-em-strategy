import requests
import json
import pandas as pd

with open("cbs_config.json") as f:
    config = json.load(f)

POOL_ID = config["poolId"]
COOKIE_PID = config["cookiePid"]


def get_nextjs_data():
    url = "https://picks.cbssports.com/_next/data/1763480815229/football/pickem/pools/{pool_id}.json"
    params = {"poolId": POOL_ID}
    cookies = {
        "pid": COOKIE_PID,
    }

    response = requests.get(url.format(pool_id=POOL_ID), params=params, cookies=cookies)
    response.raise_for_status()
    return response.json()


def refs_to_data(game, apollo_state):
    awayMoneyLine = None
    homeMoneyLine = None

    for ml_ref in apollo_state[game["oddsMarketRef"]]["moneyLines"]:
        ref = ml_ref["__ref"]
        if "AWAY" in ref:
            awayMoneyLine = int(apollo_state[ref]["odds"])
        elif "HOME" in ref:
            homeMoneyLine = int(apollo_state[ref]["odds"])

    away_pick_percent = (
        float(apollo_state[game["eventExtraRef"]]["awayTeamPickemPercentOwned"]) / 100
    )
    home_pick_percent = (
        float(apollo_state[game["eventExtraRef"]]["homeTeamPickemPercentOwned"]) / 100
    )

    away_team = apollo_state[game["awayTeamRef"]]
    home_team = apollo_state[game["homeTeamRef"]]

    return pd.Series(
        {
            "Away": f"{away_team["location"]} {away_team["nickName"]}",
            "Home": f"{home_team["location"]} {home_team["nickName"]}",
            "Away Pick %": away_pick_percent,
            "Home Pick %": home_pick_percent,
            "BetMGM Away ML": awayMoneyLine,
            "BetMGM Home ML": homeMoneyLine,
        }
    )


def get_pick_data():
    nextjs_data = get_nextjs_data()
    apollo_state = nextjs_data["pageProps"]["__APOLLO_STATE__"]
    games = []
    oddsMarketInput = {"input": {"poolId": POOL_ID}}
    oddsMarketKey = f"oddsMarket({json.dumps(oddsMarketInput, separators=(',', ':'))})"
    for state_key, state_value in apollo_state.items():
        if "PoolEvent" in state_key:
            if state_value["isLocked"] == False:
                games.append(
                    {
                        "awayTeamRef": state_value["awayTeam"]["__ref"],
                        "homeTeamRef": state_value["homeTeam"]["__ref"],
                        "eventExtraRef": state_value["extra"]["__ref"],
                        "oddsMarketRef": state_value[oddsMarketKey]["__ref"],
                    }
                )

    return pd.DataFrame(games).apply(lambda x: refs_to_data(x, apollo_state), axis=1)


if __name__ == "__main__":
    print(get_pick_data())
