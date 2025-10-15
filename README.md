# NFL Pick 'Em
Collection of scripts to help make picks in a CBS NFL Pick 'Em pool.

# Setup
Run `uv sync` to download dependencies.
Copy `cbs_config.template.json` to a new file called `cbs_config.json` and fill in the values.
To find your Pool ID, navigate to the standings page of your pool and check the URL. It should look something like: `https://picks.cbssports.com/football/pickem/pools/<pool id here>/standings/weekly`. The Pool ID is the string of characters between `/pools` and `/standings`.
To get your Cookie PID, open the Network tab of the Developer Tools in your browser and filter for XHR requests. Click a request and look at the headers, and you should see a `pid=<some string>`.

# Strategy
For a straight up Pick 'Em pool, you want to maximize the likelihood of picking each game correctly.
This is straightforward, simply pick the team which is favored by Vegas.
However, this might lead to your picks being too similar to everyone elses picks, so we might want to pick the underdog in some cases.
We don't want to pick too many underdogs as that will sacrifice our long term expected wins.
We can take advantage of the Pick Percentage to pick slight underdogs that are not being picked as often as they should.

# Knapsack
```
uv run knapsack.py
```
You can also specify a risk factor (0-100).
```
uv run knapsack.py 12.5
```
The risk factor determines the maximum amount of expected wins you are willing to sacrifice in order to increase the uniqueness of your picks.
Let's say in a given week there are 16 games to pick.
If you were to pick all favorites, you would maximize the expected correct picks for this week.
Based on the Vegas moneylines, the expected correct picks would come out to some value. For this example let's assume that it comes out to 12.0.
A risk factor of 12.5 would then allow you to sacrifice `12 * 12.5 / 100 = 1.5` wins in order to increase the uniqueness of your picks.

# Monte Carlo
```
uv run monte_carlo.py
```
This runs a simulation of the week, both in terms of your likelihood of picking games correctly and what other users in the pool have picked.
Once the simulation has finished, run `explore.py` to see the results.
```
uv run explore.py
```
