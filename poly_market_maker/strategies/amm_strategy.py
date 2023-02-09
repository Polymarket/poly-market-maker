from ..market import Token, Market, Collateral
from ..orderbook import OrderBook
from ..constants import MIN_SIZE
from ..order import Order

from .amm import AMMManager
from .base_strategy import BaseStrategy


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
        market: Market,
        config: dict,
    ):
        assert isinstance(config, dict)

        self.amm_manager = AMMManager(
            token_id_a=market.token_id(Token.A),
            token_id_b=market.token_id(Token.B),
            p_min=config.get("p_min"),
            p_max=config.get("p_max"),
            delta=config.get("delta"),
            spread=config.get("spread"),
            depth=config.get("depth"),
        )

        BaseStrategy.__init__(self, market)

    def synchronize(self, orderbook, token_prices):
        """
        Synchronize the orderbook by cancelling all orders and placing new orders
        """
        self.logger.debug("Synchronizing AMM strategy...")

        (orders_to_cancel, orders_to_place) = self.get_orders(
            orderbook, token_prices
        )

        self.cancel_orders(orders_to_cancel)
        self.place_orders(orders_to_place)

    def get_orders(self, orderbook: OrderBook, target_prices):
        orders_to_cancel = []
        orders_to_place = []

        expected_orders = self.amm_manager.get_expected_orders(
            orderbook.balances[Token.A],
            orderbook.balances[Token.B],
            orderbook.balances[Collateral],
            target_prices[Token.A],
            target_prices[Token.B],
        )
        expected_order_types = set(
            OrderType(order) for order in expected_orders
        )

        orders_to_cancel += list(
            filter(
                lambda order: OrderType(order) not in expected_order_types,
                orderbook.orders,
            )
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

            # if open_size too big, cancel all orders of this type
            if open_size > expected_size:
                orders_to_cancel += open_orders
                new_size = expected_size
            # otherwise get the remaining size
            else:
                new_size = round(expected_size - open_size, 2)

            if new_size >= MIN_SIZE:
                orders_to_place += [
                    self._new_order_from_order_type(order_type, new_size)
                ]

        return (orders_to_cancel, orders_to_place)

    @staticmethod
    def _new_order_from_order_type(
        order_type: OrderType, size: float
    ) -> Order:
        return Order(
            price=order_type.price,
            size=size,
            side=order_type.side,
            token_id=order_type.token_id,
        )
