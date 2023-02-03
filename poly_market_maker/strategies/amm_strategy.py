from ..market import Token, Market, Collateral
from ..orderbook import OrderBookManager
from ..price_feed import PriceFeed

from .amm import AMM
from .strategy import Strategy
from ..constants import MIN_SIZE

P_MIN = 0.05
P_MAX = 0.95
DELTA = 0.05


class AMMStrategy(Strategy):
    def __init__(
        self,
        price_feed: PriceFeed,
        market: Market,
        order_book_manager: OrderBookManager,
    ):
        Strategy.__init__(
            self,
            price_feed=price_feed,
            market=market,
            order_book_manager=order_book_manager,
        )
        self.amm = AMM(p_min=P_MIN, p_max=P_MAX, delta=DELTA)

    def synchronize(
        self,
    ):
        """
        Synchronize the orderbook by cancelling all orders and placing new orders
        """
        self.logger.debug("Synchronizing amm strategy...")

        orderbook = self.order_book_manager.get_order_book()

        collateral_balance = orderbook.balance(Collateral)
        token_a_balance = orderbook.balance(Token.A)
        token_b_balance = orderbook.balance(Token.B)
        if (
            collateral_balance is None
            or token_a_balance is None
            or token_b_balance is None
        ):
            self.logger.debug("Balances invalid/non-existent")
            return

        token_id_a = self.market.token_id(Token.A)
        token_id_b = self.market.token_id(Token.B)
        price_a = self.price_feed.get_price(token_id_a)
        price_b = 1 - price_a

        sell_orders_a = self.amm.get_sell_orders(
            token_a_balance, price_a, token_id_a
        )
        sell_orders_b = self.amm.get_sell_orders(
            token_b_balance, price_b, token_id_b
        )

        best_ask_a = sell_orders_a[0].size
        best_ask_b = sell_orders_b[0].size

        collateral_allocation_a = self.amm.collateral_allocation_a(
            collateral_balance, price_a, best_ask_a, best_ask_b
        )
        collateral_allocation_b = collateral_balance - collateral_allocation_a

        buy_orders_a = self.amm.get_buy_orders(
            collateral_allocation_a, price_a, token_id_a
        )
        buy_orders_b = self.amm.get_buy_orders(
            collateral_allocation_b, price_b, token_id_b
        )

        # cancel all orders
        if len(orderbook.orders) > 0:
            self.order_book_manager.cancel_orders(orderbook.orders)
            return

        # Do not place new orders if order book state is not confirmed
        if orderbook.orders_being_placed or orderbook.orders_being_cancelled:
            self.logger.debug(
                "Order book sync is in progress, not placing new orders"
            )
            return

        new_orders = [
            order
            for order in buy_orders_a
            + buy_orders_b
            + sell_orders_a
            + sell_orders_b
            if order.size > MIN_SIZE
        ]
        if len(new_orders) > 0:
            self.logger.info(f"About to place {len(new_orders)} new orders!")
            self.order_book_manager.place_orders(new_orders)

        self.logger.debug("Synchronized orderbook!")
