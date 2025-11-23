import pandas as pd

df = pd.read_parquet("cache.parquet")
df["Outright and Tied"] = df["Outright First"] + df["Tied First"]
max_exp_wins = df["Expected Wins"].max()
relevant_picks = df[df["Expected Wins"] > max_exp_wins * 0.99]
print(df.sort_values("Average Rank"))
print(relevant_picks.sort_values("Outright and Tied", ascending=False).transpose())
