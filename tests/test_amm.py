import json
from re import M
from unittest import TestCase, mock
from web3 import Web3
from poly_market_maker.market import Market, Token, Collateral
from poly_market_maker.strategies.amm import AMM


class TestAMM(TestCase):
    token_id = 1

    def test_get_buy_orders(self):
        amm = AMM(
            token_id=self.token_id,
            p_min=0.05,
            p_max=0.95,
            delta=0.01,
            depth=0.2,
            spread=0.05,
        )
        amm.set_price(0.5)
        buy_orders = amm.get_buy_orders(1000)
        self.assertEqual(len(buy_orders), 21)

        sell_orders = amm.get_sell_orders(1000)
        self.assertEqual(len(sell_orders), 21)

    def test_get_sell_size(self):
        p = 0.5
        depth = 0.05
        p_max = depth + p
        size = 1000
        delta = 0.01
        spread = 0.02

        amm = AMM(
            token_id=self.token_id,
            p_min=0.05,
            p_max=p_max,
            delta=delta,
            depth=depth,
            spread=spread,
        )

        sell_size = amm.sell_size(size, p, p_max, p_max)
        self.assertEqual(sell_size, size)

    def test_get_buy_size(self):
        p = 0.5
        depth = 0.05
        p_min = p - depth
        p_max = 0.95
        collateral = 1000
        delta = 0.01
        spread = 0.02

        amm = AMM(
            token_id=self.token_id,
            p_min=p_min,
            p_max=p_max,
            delta=delta,
            depth=depth,
            spread=spread,
        )

        buy_size = amm.buy_size(collateral, p, p_min, p_min)
        self.assertLess(buy_size * p_min, collateral)
        self.assertGreater(buy_size * p, collateral)

    def test_set_price(self):
        p = 0.5
        depth = 0.05
        p_min = 0.05
        p_max = 0.95
        delta = 0.01
        spread = 0.02

        amm = AMM(
            token_id=self.token_id,
            p_min=p_min,
            p_max=p_max,
            delta=delta,
            depth=depth,
            spread=spread,
        )
        amm.set_price(p)

        self.assertEqual(amm.p_l, 0.43)
        self.assertEqual(amm.buy_prices, [0.48, 0.47, 0.46, 0.45, 0.44, 0.43])

        self.assertEqual(amm.p_u, 0.57)
        self.assertEqual(amm.sell_prices, [0.52, 0.53, 0.54, 0.55, 0.56, 0.57])
