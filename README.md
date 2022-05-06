[![Tests](https://github.com/Polymarket/poly-market-maker/actions/workflows/tests.yaml/badge.svg?branch=main)](https://github.com/Polymarket/poly-market-maker/actions/workflows/tests.yaml)
## poly-market-maker

Market maker keeper for the Polymarket CLOB

Requires:
- Python 3.9.10
- virtualenv


### Usage

- Install dependencies: `make init`

- Create a `.env` file. See `.env.example`

- Create a `bands.json` configuration file. See the existing `bands.json`

- Start the keeper with `./run_keeper.sh`

### NBA Games

- [Readme](market_maker_nba_game.md)

- [How to run a new bot for a game](https://www.notion.so/polymarket/Run-a-market-maker-bot-for-an-NBA-game-d6e4ac0cffe943a886d2e3b57d6c6d40)

- [Logs](https://metrics-clob-staging.polymarket.com/d/LTmCw4w7k/logs?orgId=1&var-app=mmk-nba-game-271cf1e73a4e2caa33331ef15ace8bc1)

- [Bot metrics](https://metrics-clob-staging.polymarket.com/d/Eac_1eNmmk/market-maker?orgId=1&from=now-15m&to=now)