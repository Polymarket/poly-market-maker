from ..market import Token, Market, Collateral
from ..orderbook import OrderBookManager
from ..price_feed import PriceFeed

from .amm import AMMManager
from .base_strategy import BaseStrategy
from ..orderbook import OrderBook
from ..constants import MIN_SIZE
from ..order import Order

P_MIN = 0.05
P_MAX = 0.95
DELTA = 0.01
DEPTH = 0.1
SPREAD = 0.03


class OrderType:
    def __init__(self, order: Order):
        self.price = order.price
        self.side = order.side
        self.token_id = order.token_id

    def __eq__(self, other):
        if isinstance(other, OrderType):
            return (
                self.price == other.price
                and self.side == other.side
                and self.token_id == other.token_id
            )
        return False

    def __hash__(self):
        return hash((self.price, self.side, self.token_id))


class AMMStrategy(BaseStrategy):
    def __init__(
        self,
        price_feed: PriceFeed,
        market: Market,
        order_book_manager: OrderBookManager,
    ):
        BaseStrategy.__init__(
            self,
            price_feed=price_feed,
            market=market,
            order_book_manager=order_book_manager,
        )
        self.amm_manager = AMMManager(
            token_id_a=self.market.token_id(Token.A),
            token_id_b=self.market.token_id(Token.B),
            p_min=P_MIN,
            p_max=P_MAX,
            delta=DELTA,
            spread=SPREAD,
            depth=DEPTH,
        )

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

        price_a = self.price_feed.get_price(self.market.token_id(Token.A))
        price_b = 1 - price_a

        expected_orders = self.amm_manager.get_orders(
            price_a,
            price_b,
            token_a_balance,
            token_b_balance,
            collateral_balance,
        )

        orders_to_cancel = self.get_orders_to_cancel(
            orderbook, expected_orders
        )
        if len(orders_to_cancel) > 0:
            self.logger.info(
                f"About to cancel {len(orders_to_cancel)} existing orders!"
            )
            self.order_book_manager.cancel_orders(orders_to_cancel)
            return

        # Do not place new orders if order book state is not confirmed
        if orderbook.orders_being_placed or orderbook.orders_being_cancelled:
            self.logger.debug(
                "Order book sync is in progress, not placing new orders"
            )
            return

        orders_to_place = self.get_orders_to_place(orderbook, expected_orders)
        if len(orders_to_place) > 0:
            self.logger.info(
                f"About to place {len(orders_to_place)} new orders!"
            )
            self.order_book_manager.place_orders(orders_to_place)

        self.logger.debug("Synchronized orderbook!")

    @staticmethod
    def _order_from_order_type(order_type: OrderType, size: float) -> Order:
        return Order(
            price=order_type.price,
            size=size,
            side=order_type.side,
            token_id=order_type.token_id,
        )

    def get_orders_to_cancel(
        self,
        orderbook: OrderBook,
        expected_orders: list[Order],
    ):
        orders_to_cancel = []
        expected_order_types = set(
            OrderType(order) for order in expected_orders
        )
        # check if too much size per type
        for order_type in expected_order_types:
            open_orders = [
                order
                for order in orderbook.orders
                if OrderType(order) == order_type
            ]
            open_size = sum(order.size for order in open_orders)
            expected_size = sum(
                order.size
                for order in expected_orders
                if OrderType(order) == order_type
            )
            for order in sorted(
                open_orders, key=lambda o: o.size, reverse=True
            ):
                if open_size <= expected_size:
                    break
                orders_to_cancel += [order]
                open_size -= order.size

        # cancel all orders without an expected type
        orders_to_cancel += [
            order
            for order in orderbook.orders
            if OrderType(order) not in expected_order_types
        ]
        return orders_to_cancel

    def get_orders_to_place(
        self, orderbook: OrderBook, expected_orders: list[Order]
    ):
        orders_to_place = []
        expected_order_types = set(
            OrderType(order) for order in expected_orders
        )
        for order_type in expected_order_types:
            open_orders = [
                order
                for order in orderbook.orders
                if OrderType(order) == order_type
            ]
            open_size = sum(order.size for order in open_orders)
            expected_size = sum(
                order.size
                for order in expected_orders
                if OrderType(order) == order_type
            )

            remaining_size = expected_size - open_size
            orders_to_place += self.batch_order(order_type, remaining_size)

        return orders_to_place

    def batch_order(self, order_type: OrderType, size: float) -> Order:
        batched_order = []

        if size < MIN_SIZE:
            return batched_order

        min_size_orders = int(size / MIN_SIZE) - 1
        extra_order_size = round(size - min_size_orders * MIN_SIZE, 2)

        if extra_order_size >= MIN_SIZE:
            batched_order += [
                self._order_from_order_type(order_type, extra_order_size)
            ]

        if min_size_orders > 0:
            batched_order += min_size_orders * [
                self._order_from_order_type(order_type, MIN_SIZE)
            ]

        return batched_order
