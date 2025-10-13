import numpy as np

from monte_carlo import vig_adj_prob
from cbs_data import get_pick_data
import argparse


def knapsack_solver(df, budget):
    n = len(df)
    costs = df["Cost"].values
    values = df["Value"].values

    # Discretize costs for DP table (since costs are floats)
    scale = 1000
    int_costs = (costs * scale).astype(int)
    int_budget = int(budget * scale)

    # DP table
    dp = np.zeros((n + 1, int_budget + 1))
    keep = np.zeros((n, int_budget + 1), dtype=bool)

    for i in range(1, n + 1):
        for w in range(int_budget + 1):
            if int_costs[i - 1] <= w:
                if dp[i - 1][w] < dp[i - 1][w - int_costs[i - 1]] + values[i - 1]:
                    dp[i][w] = dp[i - 1][w - int_costs[i - 1]] + values[i - 1]
                    keep[i - 1][w] = True
                else:
                    dp[i][w] = dp[i - 1][w]
            else:
                dp[i][w] = dp[i - 1][w]

    # Backtrack to find which items to pick
    w = int_budget
    chosen = np.zeros(n, dtype=bool)
    for i in range(n - 1, -1, -1):
        if keep[i][w]:
            chosen[i] = True
            w -= int_costs[i]

    return chosen


def pick_team(row):
    if row["Pick Underdog"] == True:
        if row["Favorite"] == "Home":
            pick = row["Away"]
        else:
            pick = row["Home"]
    else:
        pick = row[row["Favorite"]]
    return pick


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NFL Pick'em Knapsack Solver")
    parser.add_argument("--risk", type=float, default=1.0, help="Risk percentage (float between 0 and 100)")
    args = parser.parse_args()

    risk_percentage = max(0.0, min(args.risk, 100.0)) / 100
    df = get_pick_data()
    df[["Away Prob", "Home Prob"]] = df.apply(
        lambda x: vig_adj_prob(x["Away ML"], x["Home ML"]), axis=1, result_type="expand"
    )

    # Cost in expected wins of choosing the underdog
    df["Favorite"] = np.where(df["Home Prob"] >= df["Away Prob"], "Home", "Away")
    df["Cost"] = (df["Home Prob"] - df["Away Prob"]).abs()
    df["Value"] = np.where(
        df["Favorite"] == "Home",
        df["Home Pick %"] - df["Away Pick %"],
        df["Away Pick %"] - df["Home Pick %"],
    )

    max_expected_wins = df[["Away Prob", "Home Prob"]].max(axis=1).sum()
    print(f"Max Expected Wins: {max_expected_wins:.2f}")
    df["Pick Underdog"] = knapsack_solver(df, max_expected_wins * risk_percentage)
    df["Pick"] = df.apply(pick_team, axis=1)

    print(df)
