import logging
from math import sqrt
from ..order import Order, Side
from ..utils import math_round_down


class AMM:
    def __init__(
        self,
        token_id: str,
        p_min: float,
        p_max: float,
        delta: float,
        depth: float,
        spread: float,
    ):
        self.logger = logging.getLogger(self.__class__.__name__)

        assert isinstance(token_id, str)
        assert isinstance(p_min, float)
        assert isinstance(p_max, float)
        assert isinstance(delta, float)
        assert isinstance(depth, float)
        assert isinstance(spread, float)

        self.token_id = token_id
        self.p_min = p_min
        self.p_max = p_max
        self.delta = delta
        self.spread = spread
        self.depth = depth

    def set_price(self, p_i: float):
        self.p_i = p_i
        self.p_u = round(min(p_i + self.spread + self.depth, self.p_max), 2)
        self.p_l = round(max(p_i - self.spread - self.depth, self.p_min), 2)

        self.buy_prices = []
        price = round(self.p_i - self.spread, 2)
        while price >= self.p_l:
            self.buy_prices.append(price)
            price = round(price - self.delta, 2)

        self.sell_prices = []
        price = round(self.p_i + self.spread, 2)
        while price <= self.p_u:
            self.sell_prices.append(price)
            price = round(price + self.delta, 2)

    def get_sell_orders(self, x):
        sizes = [
            # round down to avoid too large orders
            math_round_down(size, 2)
            for size in self.diff(
                [self.sell_size(x, p_t) for p_t in self.sell_prices]
            )
        ]

        orders = [
            Order(
                price=price,
                side=Side.SELL,
                token_id=self.token_id,
                size=size,
            )
            for (price, size) in zip(self.sell_prices, sizes)
        ]

        return orders

    def get_buy_orders(self, y):
        sizes = [
            # round down to avoid too large orders
            math_round_down(size, 2)
            for size in self.diff(
                [self.buy_size(y, p_t) for p_t in self.buy_prices]
            )
        ]

        orders = [
            Order(
                price=price,
                side=Side.BUY,
                token_id=self.token_id,
                size=size,
            )
            for (price, size) in zip(self.buy_prices, sizes)
        ]

        return orders

    def phi(self):
        return (1 / (sqrt(self.p_i) - sqrt(self.p_l))) * (
            1 / sqrt(self.buy_prices[0]) - 1 / sqrt(self.p_i)
        )

    def sell_size(self, x, p_t):
        return self._sell_size(x, self.p_i, p_t, self.p_u)

    @staticmethod
    def _sell_size(x, p_i, p_t, p_u):
        L = x / (1 / sqrt(p_i) - 1 / sqrt(p_u))
        a = L / sqrt(p_u) - L / sqrt(p_t) + x
        return a

    def buy_size(self, y, p_t):
        return self._buy_size(y, self.p_i, p_t, self.p_l)

    @staticmethod
    def _buy_size(y, p_i, p_t, p_l):
        L = y / (sqrt(p_i) - sqrt(p_l))
        a = L * (1 / sqrt(p_t) - 1 / sqrt(p_i))
        return a

    @staticmethod
    def diff(arr: list[float]) -> list[float]:
        return [
            arr[i] if i == 0 else arr[i] - arr[i - 1] for i in range(len(arr))
        ]


class AMMManager:
    def __init__(
        self,
        token_id_a: str,
        token_id_b: str,
        p_min: float,
        p_max: float,
        delta: float,
        spread=0.02,
        depth=1.0,
    ):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.amm_a = AMM(
            token_id=token_id_a,
            p_min=p_min,
            p_max=p_max,
            delta=delta,
            spread=spread,
            depth=depth,
        )
        self.amm_b = AMM(
            token_id=token_id_b,
            p_min=p_min,
            p_max=p_max,
            delta=delta,
            spread=spread,
            depth=depth,
        )

    def get_expected_orders(
        self, p_a: float, p_b: float, x_a: float, x_b: float, y: float
    ):
        self.amm_a.set_price(p_a)
        self.amm_b.set_price(p_b)

        sell_orders_a = self.amm_a.get_sell_orders(x_a)
        sell_orders_b = self.amm_b.get_sell_orders(x_b)

        (y_a, y_b) = self.collateral_allocation(
            y,
            sell_orders_a[0],
            sell_orders_b[0],
        )

        buy_orders_a = self.amm_a.get_buy_orders(y_a)
        buy_orders_b = self.amm_b.get_buy_orders(y_b)

        orders = sell_orders_a + sell_orders_b + buy_orders_a + buy_orders_b

        return orders

    def collateral_allocation(
        self, y: float, first_sell_order_a: Order, first_sell_order_b: Order
    ):

        y_a = (
            first_sell_order_a.size
            - first_sell_order_b.size
            + y * self.amm_b.phi()
        ) / (self.amm_a.phi() + self.amm_b.phi())

        if y_a < 0:
            y_a = 0
        elif y_a > y:
            y_a = y
        y_b = y - y_a

        return (math_round_down(y_a, 2), math_round_down(y_b, 2))

    @staticmethod
    def _get_best_ask_size(orders):
        return next(
            (
                order.size
                for order in sorted(
                    orders, key=lambda o: o.price, reverse=False
                )
            ),
            0,
        )
