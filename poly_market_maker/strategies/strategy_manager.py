from enum import Enum
import json

from ..market import Market
from ..orderbook import OrderBookManager
from ..price_feed import PriceFeed

from .base_strategy import BaseStrategy
from .amm_strategy import AMMStrategy
from .bands_strategy import BandsStrategy


class StrategyManager:
    @staticmethod
    def get_strategy(
        strategy: str,
        price_feed: PriceFeed,
        market: Market,
        order_book_manager: OrderBookManager,
        config_path: str,
    ) -> BaseStrategy:
        with open(config_path) as fh:
            config = json.load(fh)

        match Strategy(strategy):
            case Strategy.AMM:
                return AMMStrategy(
                    price_feed, market, order_book_manager, config
                )
            case Strategy.BANDS:
                return BandsStrategy(
                    price_feed, market, order_book_manager, config
                )
            case _:
                raise Exception("Invalid strategy")


class Strategy(Enum):
    AMM = "amm"
    BANDS = "bands"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            for strategy in Strategy:
                if value.lower() == strategy.value.lower():
                    return strategy
        return super()._missing_(value)
