# NBA Market maker

Adding a way to choose the price feed for the market. It can be the `clob` or an `odds` API.

## How to run it

We have to add these parameters:
```env
ODDS_API_URL= 
ODDS_API_KEY= # The key provided to request the API
ODDS_API_SPORT= # The sport key obtained from calling the /sports endpoint. upcoming is always valid, returning any live games as well as the next 8 upcoming games across all sports.
ODDS_API_REGION= # Determines the bookmakers to be returned. Valid regions are us (United States), uk (United Kingdom), au (Australia) and eu (Europe). Multiple regions can be specified if comma delimited.
ODDS_API_MARKET= # Determines which odds market is returned. Defaults to h2h (head to head / moneyline). Valid markets are h2h (moneyline), spreads (points handicaps), totals (over/under) and outrights (futures).
ODDS_API_MATCH_ID= # The identifier of the match, we need to find a way to obtain this easily
ODDS_API_TEAM_NAME= # This is the relation with our token_id. The name of the team that wins considering our token_id
```

### Team name

These markets will be something like: **Will team A beat team B?**

- `YES` token represents the winning of team A
- `NO` token represents the winning of team B

If we run a bot using this parameters:

- `match_id='123'`
- `team_name='team B'`

We are working with the `NO` token and fetching its prices from the `odds` API.

## How it works

### Having a game

```json
{
  "question": "Will Dallas Mavericks will beat Phoenix Suns?",
  "outcomes": [
    {
      "name": "Dallas Mavericks",
      "price": 225
    },
    {
      "name": "Phoenix Suns",
      "price": -265
    }
  ]
}
```
*This JSON shows the price for the winning of each team, we will convert that to possibilities later.*

### There are two instances of market makers bots running

#### For YES token

YES token means that ***Dallas Mavericks*** wins.

```env
...

price_feed_source=odds_api
team_name="Dallas Mavericks"
tokenId=0xYES
```


#### For NO token

NO token means that ***Dallas Mavericks*** loses.

```env
...

price_feed_source=odds_api
team_name="Phoenix Suns"
tokenId=0xNO
```

#### Prices calculation

The market maker bot fetches the price data from the odds api and apply the next calculations:

```python
def fromMoneyLine(d:float):
  if d < 0:
    return (-1*d)/((-1*d)+100)
  else:
    return 100/(100+d)
```

*func created considering https://www.bettingexpert.com/academy/advanced-betting-theory/odds-conversion-to-percentage*

##### For YES token

```python
midPrice = fromMoneyLine(225)

# midPrice -> 0.3076923076923077
```


##### For NO token

```python
midPrice = fromMoneyLine(-265)

# midPrice -> 0.726027397260274
```

Both market makers bots do the usual calculations to create/cancel orders using these mid prices.

### API quota

We have some limits around the `odds` requests that we can do. That's depend on which plan we pick.

There is a metric that the bot collects that shows the remaining amount of requests that we have for the current month. This metric will be shown on Grafana, also, an alarm will be created to alert us in the case of low level of requests remaining.

## Next steps

Make the execution and automation easier.