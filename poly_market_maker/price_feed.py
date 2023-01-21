import enum
import logging

from poly_market_maker.clob_api import ClobApi
from poly_market_maker.odds_api import OddsAPI
from poly_market_maker.fpmm import FPMM


class PriceFeedSource(enum.Enum):
    CLOB = "clob"
    ODDS_API = "odds_api"
    FPMM = "fpmm"


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

        if not clob_api:
            self.logger.fatal('clob_api parameter is mandatory')
            raise Exception('clob_api parameter is mandatory')

        self.clob_api = clob_api

    def get_price(self) -> float:
        self.logger.debug("Fetching target price using the clob midpoint price...")
        target_price = self.clob_api.get_price()
        self.logger.debug(f"target_price: {target_price}")
        return target_price


class PriceFeedOddsAPI(PriceFeed):
    """Resolves the prices retriving the odds api"""

    def __init__(self, odds_api: OddsAPI, match_id: str, team_name: str):
        super().__init__()

        if not odds_api:
            self.logger.fatal('odds_api parameter is mandatory')
            raise Exception('odds_api parameter is mandatory')

        if not match_id or not len(match_id):
            self.logger.fatal('match_id parameter is mandatory and can not be empty')
            raise Exception('match_id parameter is mandatory and can not be empty')

        if not team_name or not len(team_name):
            self.logger.fatal('team_name parameter is mandatory and can not be empty')
            raise Exception('team_name parameter is mandatory and can not be empty')

        self.odds_api = odds_api
        self.match_id = match_id
        self.team_name = team_name

    def get_price(self) -> float:
        self.logger.debug("Fetching target price from the odds api...")
        target_price = self.odds_api.get_price(self.match_id, self.team_name)
        self.logger.debug(f"target_price: {target_price}")
        return target_price


class PriceFeedFPMM(PriceFeed):
    """Gets the midpoint from the corresponding FPMM"""

    def __init__(self, fpmm: FPMM, conditional_token: str, fpmm_address: str, token_id: int, token_id_complement: int):
        super().__init__()

        if not fpmm:
            self.logger.fatal('contracts parameter is mandatory')
            raise Exception('contracts parameter is mandatory')

        if not conditional_token or not len(conditional_token):
            self.logger.fatal('conditional_token parameter is mandatory and can not be empty')
            raise Exception('conditional_token parameter is mandatory and can not be empty')

        if not fpmm_address or not len(fpmm_address):
            self.logger.fatal('fpmm parameter is mandatory and can not be empty')
            raise Exception('fpmm parameter is mandatory and can not be empty')

        if not token_id:
            self.logger.fatal('token_id parameter is mandatory and can not be empty')
            raise Exception('token_id parameter is mandatory and can not be empty')

        if not token_id_complement:
            self.logger.fatal('token_id_complement parameter is mandatory and can not be empty')
            raise Exception('token_id_complement parameter is mandatory and can not be empty')
        
        self.fpmm = fpmm
        self.conditional_token = conditional_token
        self.fpmm_address = fpmm_address
        self.token_id = token_id
        self.token_id_complement = token_id_complement

    def get_price(self) -> float:
        self.logger.debug("Fetching target price from the fpmm...")
        target_price = self.fpmm.get_price(self.conditional_token, self.fpmm_address, self.token_id, self.token_id_complement)
        self.logger.debug(f"target_price: {target_price}")
        return target_price
        
