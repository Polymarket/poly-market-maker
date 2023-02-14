from enum import Enum
import logging

from poly_market_maker.clob_api import ClobApi


class PriceFeedSource(Enum):
    CLOB = "clob"


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
            self.logger.fatal("clob_api parameter is mandatory")
            raise Exception("clob_api parameter is mandatory")

        self.clob_api = clob_api

    def get_price(self, token_id) -> float:
        self.logger.debug("Fetching target price using the clob midpoint price...")
        target_price = self.clob_api.get_price(token_id)
        self.logger.debug(f"target_price: {target_price}")
        return target_price
