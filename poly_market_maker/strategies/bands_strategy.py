from .bands import Bands
from ..market import Token, Market, Collateral
from ..order import Order, Side
from ..orderbook import OrderBook, OrderBookManager
from ..price_feed import PriceFeed
from ..constants import MAX_DECIMALS
from .base_strategy import BaseStrategy


class BandsStrategy(BaseStrategy):
    def __init__(
        self,
        price_feed: PriceFeed,
        market: Market,
        order_book_manager: OrderBookManager,
        config: dict,
    ):
        assert isinstance(config, dict)

        try:
            self.bands = Bands(config.get("bands"))
        except Exception as e:
            self.logger.exception(
                f"Config is invalid ({e}). Treating the config as if it has no bands."
            )
        BaseStrategy.__init__(self, price_feed, market, order_book_manager)

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

        (orders_to_cancel, orders_to_place) = self.get_orders(orderbook)

        if len(orders_to_cancel) > 0:
            self.logger.info(
                f"About to cancel {len(orders_to_cancel)} existing orders!"
            )
            self.order_book_manager.cancel_orders(orders_to_cancel)
            return

        if len(orders_to_place) > 0:
            self.logger.info(
                f"About to place {len(orders_to_place)} new orders!"
            )
            self.order_book_manager.place_orders(orders_to_place)

        self.logger.debug("Synchronized orderbook!")

    def get_orders(self, orderbook: OrderBook):
        orders_to_place = []
        orders_to_cancel = []

        # get target prices
        target_price_a = self.price_feed.get_price(
            self.market.token_id(Token.A)
        )
        target_price_b = round(1 - target_price_a, MAX_DECIMALS)
        target_prices = {Token.A: target_price_a, Token.B: target_price_b}
        for token in Token:
            self.logger.debug(
                f"{token.value} target price: {target_prices[token]}"
            )

        # cancel orders
        for token in Token:
            orders = list(
                filter(
                    lambda order: self._filter_by_corresponding_buy_token(
                        order, token
                    ),
                    orderbook.orders,
                )
            )

            orders_to_cancel += self.bands.cancellable_orders(
                orders, target_prices[token]
            )

        # remaining open orders
        open_orders = list(set(orders) - set(orders_to_cancel))
        balance_locked_by_open_buys = sum(
            order.size * order.price
            for order in open_orders
            if order.side == Side.BUY
        )
        self.logger.debug(
            f"Collateral locked by buys: {balance_locked_by_open_buys}"
        )

        free_collateral_balance = (
            orderbook.balance(Collateral) - balance_locked_by_open_buys
        )
        self.logger.debug(
            f"Free collateral balance: {free_collateral_balance}"
        )

        # place orders
        for token in Token:
            orders = list(
                filter(
                    lambda order: self._filter_by_corresponding_buy_token(
                        order, token
                    ),
                    orderbook.orders,
                )
            )

            balance_locked_by_open_sells = sum(
                order.size for order in orders if order.side == Side.SELL
            )
            self.logger.debug(
                f"{token.complement().value} locked by sells: {balance_locked_by_open_sells}"
            )

            free_token_balance = (
                orderbook.balance(token.complement())
                - balance_locked_by_open_sells
            )
            self.logger.debug(
                f"Free {token.complement().value} balance: {free_token_balance}"
            )

            new_orders = self.bands.new_orders(
                orders,
                free_collateral_balance,
                free_token_balance,
                target_prices[token],
                self.market.token_id(token),
                self.market.token_id(token.complement()),
            )
            free_collateral_balance -= sum(
                order.size * order.price
                for order in new_orders
                if order.side == Side.BUY
            )
            orders_to_place += new_orders

        return (orders_to_cancel, orders_to_place)

    def _filter_by_corresponding_buy_token(
        self, order: Order, buy_token: Token
    ):
        order_token = self.market.token(order.token_id)
        return (order.side == Side.BUY and order_token == buy_token) or (
            order.side == Side.SELL and order_token != buy_token
        )
