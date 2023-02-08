from ..market import Token, Market, Collateral
from ..orderbook import OrderBookManager
from ..price_feed import PriceFeed

from .amm import AMMManager
from .base_strategy import BaseStrategy
from ..orderbook import OrderBook
from ..constants import MIN_SIZE
from ..order import Order, Side


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
                and int(self.token_id) == int(other.token_id)
            )
        return False

    def __hash__(self):
        return hash((self.price, self.side, self.token_id))

    def __repr__(self):
        return f"OrderType[price={self.price}, side={self.side}, token_id={self.token_id}]"


class AMMStrategy(BaseStrategy):
    def __init__(
        self,
        price_feed: PriceFeed,
        market: Market,
        order_book_manager: OrderBookManager,
        config: dict,
    ):
        assert isinstance(config, dict)
        BaseStrategy.__init__(
            self,
            price_feed=price_feed,
            market=market,
            order_book_manager=order_book_manager,
        )

        self.amm_manager = AMMManager(
            token_id_a=self.market.token_id(Token.A),
            token_id_b=self.market.token_id(Token.B),
            p_min=config.get("p_min"),
            p_max=config.get("p_max"),
            delta=config.get("delta"),
            spread=config.get("spread"),
            depth=config.get("depth"),
        )

    def synchronize(
        self,
    ):
        """
        Synchronize the orderbook by cancelling all orders and placing new orders
        """
        self.logger.debug("Synchronizing AMM strategy...")

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

        price_a = round(
            self.price_feed.get_price(self.market.token_id(Token.A)), 2
        )
        price_b = round(1 - price_a, 2)

        expected_orders = self.amm_manager.get_expected_orders(
            price_a,
            price_b,
            token_a_balance,
            token_b_balance,
            collateral_balance,
        )

        (orders_to_cancel, orders_to_place) = self.get_orders(
            orderbook, expected_orders
        )

        if len(orders_to_cancel) > 0:
            self.logger.info(
                f"About to cancel {len(orders_to_cancel)} existing orders!"
            )
            self.order_book_manager.cancel_orders(orders_to_cancel)

        if len(orders_to_place) > 0:
            self.logger.info(
                f"About to place {len(orders_to_place)} new orders!"
            )
            self.order_book_manager.place_orders(orders_to_place)

        # self.order_book_manager.wait_for_stable_order_book()
        self.logger.debug("Synchronized orderbook!")

    def get_orders(self, orderbook: OrderBook, expected_orders: list[Order]):
        orders_to_cancel = []
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

            if open_size > expected_size:
                orders_to_cancel += open_orders
                orders_to_place.append(
                    self._order_from_order_type(order_type, expected_size)
                )

            else:
                remaining_size = round(expected_size - open_size, 2)
                if remaining_size >= MIN_SIZE:
                    orders_to_place.append(
                        self._order_from_order_type(order_type, remaining_size)
                    )

        return (orders_to_cancel, orders_to_place)

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
            if remaining_size >= MIN_SIZE:
                orders_to_place += [
                    self._order_from_order_type(order_type, remaining_size)
                ]

        return orders_to_place

    @staticmethod
    def _order_from_order_type(order_type: OrderType, size: float) -> Order:
        return Order(
            price=order_type.price,
            size=size,
            side=order_type.side,
            token_id=order_type.token_id,
        )
