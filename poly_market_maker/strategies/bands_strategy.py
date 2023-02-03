from .bands import Bands
import json
from ..market import Token, Market, Collateral
from ..order import Order, Side
from ..orderbook import OrderBook, OrderBookManager
from ..price_feed import PriceFeed
from .base_strategy import BaseStrategy


class BandsStrategy(BaseStrategy):
    def __init__(
        self,
        price_feed: PriceFeed,
        market: Market,
        order_book_manager: OrderBookManager,
        config_path: str,
    ):
        BaseStrategy.__init__(self, price_feed, market, order_book_manager)
        with open(config_path) as fh:
            self.bands = Bands.read(json.load(fh))

    def synchronize(
        self,
    ):
        """
        Synchronize the orderbook by cancelling orders out of bands and placing new orders if necessary
        """
        self.logger.debug("Synchronizing bands strategy...")

        orderbook = self.order_book_manager.get_order_book()
        if (
            orderbook.balance(Collateral) is None
            or orderbook.balance(Token.A) is None
            or orderbook.balance(Token.B) is None
        ):
            self.logger.debug("Balances invalid/non-existent")
            return

        for buy_token in Token:
            orders_by_type = [
                order
                for order in orderbook.orders
                if (self._get_buy_token(order) == buy_token)
            ]

            target_price = self.price_feed.get_price(
                self.market.token_id(buy_token)
            )

            self.logger.debug(
                f"Token {buy_token.name} target price: {target_price}"
            )

            self.synchronize_token(
                orderbook, buy_token, orders_by_type, target_price
            )

        self.logger.debug("Synchronized orderbook!")

    def synchronize_token(
        self,
        orderbook: OrderBook,
        buy_token: Token,
        orders: list[Order],
        target_price: float,
    ):
        sell_token = Token.complement(buy_token)
        cancellable_orders = self.bands.cancellable_orders(
            orders=orders,
            target_price=target_price,
        )

        if len(cancellable_orders) > 0:
            self.order_book_manager.cancel_orders(cancellable_orders)
            return

        # Do not place new orders if order book state is not confirmed
        if orderbook.orders_being_placed or orderbook.orders_being_cancelled:
            self.logger.debug(
                "Order book sync is in progress, not placing new orders"
            )
            return

        balance_locked_by_open_buys = sum(
            order.size * order.price
            for order in orders
            if order.side == Side.BUY
        )
        balance_locked_by_open_sells = sum(
            order.size for order in orders if order.side == Side.SELL
        )
        self.logger.debug(
            f"Collateral locked by buys: {balance_locked_by_open_buys}"
        )
        self.logger.debug(
            f"Token {sell_token.name} locked by sells: {balance_locked_by_open_sells}"
        )

        free_collateral_balance = (
            orderbook.balance(Collateral) - balance_locked_by_open_buys
        )
        free_token_balance = (
            orderbook.balance(sell_token) - balance_locked_by_open_sells
        )

        self.logger.debug(
            f"Free collateral balance: {free_collateral_balance}"
        )
        self.logger.debug(f"Free token balance: {free_token_balance}")

        # Create new orders if needed
        new_orders = self.bands.new_orders(
            orders=orders,
            collateral_balance=free_collateral_balance,
            token_balance=free_token_balance,
            target_price=target_price,
            buy_token_id=self.market.token_id(buy_token),
            sell_token_id=self.market.token_id(sell_token),
        )

        if len(new_orders) > 0:
            self.logger.info(f"About to place {len(new_orders)} new orders!")
            self.order_book_manager.place_orders(new_orders)

    def _get_buy_token(self, order: Order):
        token = self.market.token(order.token_id)
        return token if order.side == Side.BUY else token.complement()
