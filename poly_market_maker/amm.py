import itertools
import logging
from math import sqrt
from .constants import MIN_TICK, MIN_SIZE, MAX_DECIMALS
from .order import Order, Side

from decimal import getcontext, Decimal


class AMM:
    def __init__(
        self,
        p_min: float,
        p_max: float,
        delta: float,
    ):
        self.logger = logging.getLogger(self.__class__.__name__)
        assert isinstance(p_min, float)
        assert isinstance(p_max, float)
        assert isinstance(delta, float)

        self.p_min = p_min
        self.p_max = p_max
        self.delta = delta

        self.type = type

        # getcontext().prec = 4

    def sell_size(self, x, p, pf):
        L = self.sell_liquidity(x, p)
        a = L / sqrt(self.p_max) - L / sqrt(pf) + x
        return a

    def sell_cost(self, x, p, pf):
        L = self.sell_liquidity(x, p)
        b = L * sqrt(pf) - L * sqrt(p)
        return b

    def buy_size(self, y, p, pf):
        L = self.buy_liquidity(y, p)
        a = L / sqrt(pf) - L / sqrt(p)
        return a

    def buy_cost(self, y, p, pf):
        L = self.buy_liquidity(y, p)
        b = y + L * sqrt(self.p_min) - L * sqrt(pf)
        return b

    def sell_liquidity(self, x, p):
        L = x / (1 / sqrt(p) - 1 / sqrt(self.p_max))
        return L

    def buy_liquidity(self, y, p):
        L = y / (sqrt(p) - sqrt(self.p_min))
        return L

    def phi(self, p):
        return (1 / (sqrt(p) - sqrt(self.p_min))) * (
            1 / sqrt(p - self.delta) - 1 / sqrt(p)
        )

    def buy_liq_A(self, y, p_a, sell_a, sell_b):
        return (sell_a - sell_b + y * self.phi(1 - p_a)) / (
            self.phi(p_a) + self.phi(1 - p_a)
        )

    @staticmethod
    def round(p: float):
        return float(Decimal(p).quantize(Decimal(".01")))

    def get_sell_orders(self, x, p, token_id: str):
        steps = int((self.p_max - p) / self.delta)
        prices = [
            self.round(p + self.delta * (step + 1)) for step in range(steps)
        ]
        sizes = [
            self.round(size)
            for size in self.diff([self.sell_size(x, p, pf) for pf in prices])
        ]

        orders = [
            Order(
                price=price,
                side=Side.SELL,
                token_id=token_id,
                size=size,
            )
            for (price, size) in zip(prices, sizes)
        ]

        return orders

    def get_buy_orders(self, y, p, token_id: str):
        steps = int((p - self.p_min) / self.delta)
        prices = [
            self.round(p - self.delta * (step + 1)) for step in range(steps)
        ]
        sizes = [
            self.round(size)
            for size in self.diff([self.buy_size(y, p, pf) for pf in prices])
        ]

        orders = [
            Order(
                price=price,
                side=Side.BUY,
                token_id=token_id,
                size=size,
            )
            for (price, size) in zip(prices, sizes)
        ]

        return orders

    @staticmethod
    def diff(arr: list[float]) -> list[float]:
        return [
            arr[i] if i == 0 else arr[i] - arr[i - 1] for i in range(len(arr))
        ]
