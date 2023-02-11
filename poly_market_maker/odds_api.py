import time
import logging
import requests

from .metrics import odds_api_latency, odds_api_remaining_requests


class OddsAPI:
    """Implementing https://the-odds-api.com/"""

    def __init__(
        self,
        api_key: str,
        sport: str,
        region: str,
        market: str,
        api_url: str = "https://api.the-odds-api.com/v4/sports",
    ):
        """
        Creates a client for the-odds-api

            Parameters:
                api_key (str): The key provided to request the API
                sport (str): The sport key obtained from calling the /sports endpoint. upcoming is always valid, returning any live games as well as the next 8 upcoming games across all sports. Check https://api.the-odds-api.com/v4/sports?all=true&apiKey=
                region (str): Determines the bookmakers to be returned. Valid regions are us (United States), uk (United Kingdom), au (Australia) and eu (Europe). Multiple regions can be specified if comma delimited. Check https://the-odds-api.com/sports-odds-data/bookmaker-apis.html.
                market (str): Determines which odds market is returned. Defaults to h2h (head to head / moneyline). Valid markets are h2h (moneyline), spreads (points handicaps), totals (over/under) and outrights (futures).
        """
        self.logger = logging.getLogger(self.__class__.__name__)

        if not api_key or not len(api_key):
            self.logger.fatal("api_key parameter is mandatory and can not be empty")
            raise Exception("api_key parameter is mandatory and can not be empty")

        if not sport or not len(sport):
            self.logger.fatal("sport parameter is mandatory and can not be empty")
            raise Exception("sport parameter is mandatory and can not be empty")

        if not region or not len(region):
            self.logger.fatal("region parameter is mandatory and can not be empty")
            raise Exception("region parameter is mandatory and can not be empty")

        if not market or not len(market):
            self.logger.fatal("market parameter is mandatory and can not be empty")
            raise Exception("market parameter is mandatory and can not be empty")

        if not api_url or not len(api_url):
            self.logger.fatal("api_url parameter is mandatory and can not be empty")
            raise Exception("api_url parameter is mandatory and can not be empty")

        self.api_key = api_key
        self.sport = sport
        self.region = region
        self.market = market
        self.date_format = "iso"
        self.odds_format = "american"
        self.api_url = api_url

    def get_price(self, match_id: str, team_name: str) -> float:
        odds_json = self.get_odds()

        if odds_json == None:
            return -1

        prices = []
        for match in odds_json:
            if match["id"] == match_id:
                for bookmaker in match["bookmakers"]:
                    for market in bookmaker["markets"]:
                        for outcome in market["outcomes"]:
                            if outcome["name"].lower() == team_name.lower():
                                prices.append(float(outcome["price"]))

        if len(prices) > 0:
            return sum(fromMoneyLine(price) for price in prices) / len(prices)
        else:
            return 0

    def get_odds(self) -> list:
        start_time = time.time()
        odds_response = requests.get(
            f"{self.api_url}/{self.sport}/odds",
            params={
                "api_key": self.api_key,
                "regions": self.region,
                "markets": self.market,
                "oddsFormat": self.odds_format,
                "dateFormat": self.date_format,
            },
        )

        if odds_response.status_code != 200:
            self.logger.error(
                f"Failed to get odds: status_code {odds_response.status_code}, response body {odds_response.text}"
            )
            odds_api_latency.labels(method="odds", status="error").observe(
                (time.time() - start_time)
            )
            return None

        odds_api_latency.labels(method="odds", status="ok").observe(
            (time.time() - start_time)
        )

        # store the remaining requests of our quota
        odds_api_remaining_requests.set(
            int(odds_response.headers["x-requests-remaining"])
        )

        odds_json = odds_response.json()

        return odds_json


# odds utils
def fromMoneyLine(d: float):
    if d < 0:
        return (-1 * d) / ((-1 * d) + 100)
    else:
        return 100 / (100 + d)
