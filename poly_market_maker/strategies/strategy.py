from ..market import Market
from ..orderbook import OrderBookManager
from ..price_feed import PriceFeed
import logging


class Strategy:
    def __init__(
        self,
        price_feed: PriceFeed,
        market: Market,
        order_book_manager: OrderBookManager,
    ):
        self.price_feed = price_feed
        self.market = market
        self.order_book_manager = order_book_manager

        self.logger = logging.getLogger(self.__class__.__name__)
