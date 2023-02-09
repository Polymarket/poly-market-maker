from enum import Enum
import json
import logging

from ..market import Market
from ..orderbook import OrderBookManager
from ..price_feed import PriceFeed

from .base_strategy import BaseStrategy
from .amm_strategy import AMMStrategy
from .bands_strategy import BandsStrategy

from ..market import Token, Collateral
from ..constants import MAX_DECIMALS


class StrategyManager:
    def __init__(
        self,
        strategy: str,
        config_path: str,
        price_feed: PriceFeed,
        order_book_manager: OrderBookManager,
        market: Market,
    ) -> BaseStrategy:
        self.logger = logging.getLogger(self.__class__.__name__)

        with open(config_path) as fh:
            config = json.load(fh)

        self.price_feed = price_feed
        self.order_book_manager = order_book_manager
        self.market = market

        match Strategy(strategy):
            case Strategy.AMM:
                self.strategy = AMMStrategy(market, config)
            case Strategy.BANDS:
                self.strategy = BandsStrategy(market, config)
            case _:
                raise Exception("Invalid strategy")

        self.strategy.cancel_orders_with(self.cancel_orders)
        self.strategy.place_orders_with(self.place_orders)

    def synchronize(self):
        try:
            orderbook = self.get_order_book()
        except Exception:
            return
        token_prices = self.get_token_prices()

        self.strategy.synchronize(orderbook, token_prices)
        self.logger.debug("Synchronized orderbook!")

    def get_order_book(self):
        orderbook = self.order_book_manager.get_order_book()

        if (
            orderbook.balances[Collateral] is None
            or orderbook.balances[Token.A] is None
            or orderbook.balances[Token.B] is None
        ):
            self.logger.debug("Balances invalid/non-existent")
            raise Exception("Balances invalid/non-existent")

        return orderbook

    def get_token_prices(self):
        # get target prices
        price_a = round(
            self.price_feed.get_price(self.market.token_id(Token.A)),
            MAX_DECIMALS,
        )
        price_b = round(1 - price_a, MAX_DECIMALS)
        return {Token.A: price_a, Token.B: price_b}

    def cancel_orders(self, orders_to_cancel):
        if len(orders_to_cancel) > 0:
            self.logger.info(
                f"About to cancel {len(orders_to_cancel)} existing orders!"
            )
            self.order_book_manager.cancel_orders(orders_to_cancel)
            return

    def place_orders(self, orders_to_place):
        if len(orders_to_place) > 0:
            self.logger.info(
                f"About to place {len(orders_to_place)} new orders!"
            )
            self.order_book_manager.place_orders(orders_to_place)

        self.logger.debug("Synchronized orderbook!")


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
