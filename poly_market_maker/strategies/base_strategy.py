import logging


class BaseStrategy:
    """Base market making strategy"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.place_orders = None
        self.cancel_orders = None

    def synchronize(self, orderbook, token_prices):
        pass

    def place_orders_with(self, place_orders_function):
        self.place_orders = place_orders_function

    def cancel_orders_with(self, cancel_orders_function):
        self.cancel_orders = cancel_orders_function
