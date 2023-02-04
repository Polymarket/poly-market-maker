from enum import Enum

from ..market import Market
from ..orderbook import OrderBookManager
from ..price_feed import PriceFeed
from .base_strategy import BaseStrategy

from .amm_strategy import AMMStrategy
from .bands_strategy import BandsStrategy


class Strategy(Enum):
    AMM = "amm"
    Bands = "bands"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            if value.lower() == Strategy.AMM.value.lower():
                return Strategy.AMM
            if value.lower() == Strategy.Bands.value.lower():
                return Strategy.Bands
        return super()._missing_(value)

    def init(
        self,
        price_feed: PriceFeed,
        market: Market,
        order_book_manager: OrderBookManager,
        config_path: str,
    ) -> BaseStrategy:
        match self:
            case Strategy.AMM:
                return AMMStrategy(
                    price_feed,
                    market,
                    order_book_manager,
                )
            case Strategy.Bands:
                return BandsStrategy(
                    price_feed, market, order_book_manager, config_path
                )
            case _:
                raise Exception("Invalid strategy")
