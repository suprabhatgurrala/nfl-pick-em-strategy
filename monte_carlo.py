import itertools
import pandas as pd
import numpy as np
from scipy.stats import rankdata
from tqdm import tqdm
from dask import dataframe
from dask.diagnostics import ProgressBar
from dask import delayed
from dask.distributed import Client
import dask

from cbs_data import get_pick_data


def american_to_implied(odds: int) -> float:
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return abs(odds) / (abs(odds) + 100)


def vig_adj_prob(away_ml, home_ml):
    implied_a = american_to_implied(away_ml)
    implied_h = american_to_implied(home_ml)

    implied_sum = implied_a + implied_h

    return implied_a / implied_sum, implied_h / implied_sum


def map_team_to_win_prob(row):
    team_to_win_prob[row["Away"]] = row["Away Prob"]
    team_to_win_prob[row["Home"]] = row["Home Prob"]


def simulate(input_df, num_sims=10000, num_players=16):
    print(f"Generating {num_sims:,} simulations with {num_players} other players.")
    num_games = input_df.shape[0]
    picks_sim = np.random.rand(num_games, num_players, num_sims)
    games_sim = np.random.rand(num_games, num_sims)
    pick_outcomes = (
        picks_sim > input_df["Away Pick %"].values[:, np.newaxis, np.newaxis]
    )
    picks = np.where(
        pick_outcomes,
        input_df["Home"].values[:, np.newaxis, np.newaxis],
        input_df["Away"].values[:, np.newaxis, np.newaxis],
    )
    game_outcomes = games_sim > input_df["Away Prob"].values[:, np.newaxis]
    winners = np.where(
        game_outcomes,
        input_df["Home"].values[:, np.newaxis],
        input_df["Away"].values[:, np.newaxis],
    )
    results = np.equal(picks, winners[:, np.newaxis, :]).sum(axis=0)
    return winners, results


# @delayed
def compute_stats(my_picks, winners, results):
    my_results = np.equal(np.array(my_picks)[:, np.newaxis], winners).sum(axis=0)
    concatenated_results = np.concatenate([my_results[np.newaxis, :], results], axis=0)
    ranks = rankdata(concatenated_results * -1, method="average", axis=0)
    my_ranks = ranks[0, :]
    first_count = (my_ranks == 1.0).sum()
    tied_first_count = ((my_ranks < 2) & (my_ranks > 1)).sum()
    pick_prob_dict = {}
    for i, pick in enumerate(my_picks):
        pick_prob_dict[f"Game {i + 1}"] = pick
    pick_prob_dict["Outright First"] = first_count
    pick_prob_dict["Tied First"] = tied_first_count
    pick_prob_dict["Expected Wins"] = pd.Series(my_picks).map(team_to_win_prob).sum()
    pick_prob_dict["Average Wins"] = my_results.mean()
    pick_prob_dict["Average Rank"] = my_ranks.mean()
    return pick_prob_dict


if __name__ == "__main__":
    df = get_pick_data()
    df[["Away Prob", "Home Prob"]] = df.apply(
        lambda x: vig_adj_prob(x["Away ML"], x["Home ML"]), axis=1, result_type="expand"
    )
    team_to_win_prob = {}
    df.apply(map_team_to_win_prob, axis=1)
    # TODO: daskify winners and results which should reduce memory footprint when parallelizing
    winners, results = simulate(df)

    permutations_iterator = itertools.product(*zip(df["Away"], df["Home"]))

    client = Client(n_workers=12)
    results_dict = []
    print("Testing all permutations:")
    for pick_permutation in tqdm(permutations_iterator, total=2 ** df.shape[0]):
        results_dict.append(compute_stats(pick_permutation, winners, results))

    # with ProgressBar():
    #      dask.compute(results_dict)

    output_df = pd.DataFrame(results_dict)
    print(output_df)
    output_df.to_parquet("cache.parquet")
    print("Wrote to cache.parquet")
