import json
from re import M
from unittest import TestCase, mock
from web3 import Web3
from poly_market_maker.market import Market, Token, Collateral
from poly_market_maker.strategies.amm import AMMManager
from poly_market_maker.order import Order, Side


class TestAMM(TestCase):
    token_id_a = "123"
    token_id_b = "456"

    def test_get_expected_orders(self):
        p = 0.5
        depth = 0.05
        p_min = 0.05
        p_max = 0.95
        delta = 0.01
        spread = 0.02

        amm_manager = AMMManager(
            token_id_a=self.token_id_a,
            token_id_b=self.token_id_b,
            p_min=p_min,
            p_max=p_max,
            delta=delta,
            depth=depth,
            spread=spread,
        )

        orders = amm_manager.get_expected_orders(p, p, 1000, 1000, 2000)
        self.assertTrue(len(orders) > 0)

        sell_orders = [order for order in orders if order.side == Side.SELL]
        buy_orders = [order for order in orders if order.side == Side.BUY]

        sell_orders_a = [
            order for order in sell_orders if order.token_id == self.token_id_a
        ]
        sell_orders_b = [
            order for order in sell_orders if order.token_id == self.token_id_b
        ]
        buy_orders_a = [
            order for order in buy_orders if order.token_id == self.token_id_a
        ]
        buy_orders_b = [
            order for order in buy_orders if order.token_id == self.token_id_b
        ]

        sell_prices_a = [order.price for order in sell_orders_a]
        self.assertEqual(sell_prices_a, [0.52, 0.53, 0.54, 0.55, 0.56, 0.57])
        sell_prices_b = [order.price for order in sell_orders_b]
        self.assertEqual(sell_prices_b, [0.52, 0.53, 0.54, 0.55, 0.56, 0.57])

        buy_prices_a = [order.price for order in buy_orders_a]
        self.assertEqual(buy_prices_a, [0.48, 0.47, 0.46, 0.45, 0.44, 0.43])
        buy_prices_b = [order.price for order in buy_orders_b]
        self.assertEqual(buy_prices_b, [0.48, 0.47, 0.46, 0.45, 0.44, 0.43])
