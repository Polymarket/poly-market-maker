import enum
import logging

from poly_market_maker.clob_api import ClobApi
from poly_market_maker.odds_api import OddsAPI


class PriceFeedSource(enum.Enum):
    CLOB = "clob"
    ODDS_API = "odds_api"


class PriceFeed:
    """Market mid price resolvers"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_price(self) -> float:
        raise NotImplemented()


class PriceFeedClob(PriceFeed):
    """Resolves the prices from the clob"""

    def __init__(self, clob_api: ClobApi):
        super().__init__()

        self.clob_api = clob_api

    def get_price(self) -> float:
        return self.clob_api.get_price()


class PriceFeedOddsAPI(PriceFeed):
    """Resolves the prices retriving the odds api"""

    def __init__(self, odds_api: OddsAPI, match_id: str, team_name: str):
        super().__init__()

        self.odds_api = odds_api
        self.match_id = match_id
        self.team_name = team_name

    def get_price(self) -> float:
        return self.odds_api.get_price(self.match_id, self.team_name)
