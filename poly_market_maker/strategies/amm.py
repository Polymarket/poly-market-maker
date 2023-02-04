import logging
from math import sqrt
from ..order import Order, Side


class AMM:
    def __init__(
        self,
        token_id: str,
        p_min: float,
        p_max: float,
        delta: float,
        depth=1.0,
        spread=None,
    ):
        self.logger = logging.getLogger(self.__class__.__name__)
        assert isinstance(p_min, float)
        assert isinstance(p_max, float)
        assert isinstance(delta, float)

        self.token_id = token_id
        self.p_min = p_min
        self.p_max = p_max

        self.delta = delta
        self.spread = spread if spread is not None else delta
        self.depth = depth

    def set_price(self, p_i: float):
        self.p_i = p_i
        self.p_u = min(p_i + self.depth, self.p_max)
        self.p_l = max(p_i - self.depth, self.p_min)

        buy_steps = (
            int(round(((self.p_i - self.spread) - self.p_l) / self.delta, 4))
            + 1
        )
        self.buy_prices = [
            round(p_i - self.spread - self.delta * (step), 2)
            for step in range(buy_steps)
        ]

        sell_steps = (
            int(round((self.p_u - (self.p_i + self.spread)) / self.delta, 4))
            + 1
        )
        self.sell_prices = [
            round(self.p_i + self.spread + self.delta * (step), 2)
            for step in range(sell_steps)
        ]

    def get_sell_orders(self, x):
        sizes = [
            round(size, 2)
            for size in self.diff(
                [
                    self.sell_size(x, self.p_i, p_t, self.p_u)
                    for p_t in self.sell_prices
                ]
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
            round(size, 2)
            for size in self.diff(
                [
                    self.buy_size(y, self.p_i, p_t, self.p_l)
                    for p_t in self.buy_prices
                ]
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
        p_1 = self.sell_prices[0]
        return (1 / (sqrt(self.p_i) - sqrt(self.p_l))) * (
            1 / sqrt(p_1) - 1 / sqrt(self.p_i)
        )

    @staticmethod
    def sell_size(x, p_i, p_t, p_u):
        L = x / (1 / sqrt(p_i) - 1 / sqrt(p_u))
        a = L / sqrt(p_u) - L / sqrt(p_t) + x
        return a

    @staticmethod
    def buy_size(y, p_i, p_t, p_l):
        L = y / (sqrt(p_i) - sqrt(p_l))
        a = L / sqrt(p_t) - L / sqrt(p_i)
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

    def get_orders(
        self, p_a: float, p_b: float, x_a: float, x_b: float, y: float
    ):
        self.amm_a.set_price(p_a)
        self.amm_b.set_price(p_b)

        sell_orders_a = self.amm_a.get_sell_orders(x_a)
        sell_orders_b = self.amm_b.get_sell_orders(x_b)

        (y_a, y_b) = self.collateral_allocation(
            y,
            sell_orders_a,
            sell_orders_b,
        )

        buy_orders_a = self.amm_a.get_buy_orders(y_a)
        buy_orders_b = self.amm_b.get_buy_orders(y_b)

        orders = sell_orders_a + sell_orders_b + buy_orders_a + buy_orders_b

        return orders

    def collateral_allocation(self, y, sell_orders_a, sell_orders_b):
        best_ask_size_a = self._get_best_ask_size(sell_orders_a)
        best_ask_size_b = self._get_best_ask_size(sell_orders_b)

        y_a = (best_ask_size_a - best_ask_size_b + y * self.amm_b.phi()) / (
            self.amm_a.phi() + self.amm_b.phi()
        )
        y_b = y - y_a

        return (y_a, y_b)

    @staticmethod
    def _get_best_ask_size(orders):
        return next(
            (order.size for order in sorted(orders, key=lambda o: o.price)), 0
        )
