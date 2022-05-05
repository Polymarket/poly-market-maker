# Market maker NBA games

## Having a game

```json
{
  "question": "Will Dallas Mavericks will beat Phoenix Suns?",
  "outcomes": [
    {
      "name": "Dallas Mavericks",
      "price": 225,
      "tokenId": "0xYES"
    },
    {
      "name": "Phoenix Suns",
      "price": -265,
      "tokenId": "0xNO"
    }
  ]
}
```
*to be honest this json shows the price for the winning of each team, we will convert that to possibilities later.*

## There are two instances of market makers bots running

### For YES token

YES token means that ***Dallas Mavericks*** wins.

```env
...

price_feed=oddsapi
tokenId=0xYES
```


### For NO token

NO token means that ***Dallas Mavericks*** loses.

```env
...

price_feed=oddsapi
tokenId=0xNO
```

### Prices calculation

The market maker bot fetches the price data from the odds api and apply the next calculations:

```python
def fromMoneyLine(d:float):
  if d < 0:
    return (-1*d)/((-1*d)+100)
  else:
    return 100/(100+d)
```

*func created considering https://www.bettingexpert.com/academy/advanced-betting-theory/odds-conversion-to-percentage*

#### For YES token

```python
midPrice = fromMoneyLine(225)

# midPrice -> 0.3076923076923077
```


#### For NO token

```python
midPrice = fromMoneyLine(-265)

# midPrice -> 0.726027397260274
```

Both market makers bots do the usual calculations to create/cancel orders using these mid prices.