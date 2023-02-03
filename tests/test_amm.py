import json
from re import M
from unittest import TestCase, mock
from web3 import Web3
from poly_market_maker.market import Market, Token, Collateral
from poly_market_maker.strategies.amm import AMM


class TestAMM(TestCase):
    def test_get_buy_orders(self):
        amm = AMM(p_min=0.05, p_max=0.95, delta=0.05, radius=0.2)

        buy_orders = amm.get_buy_orders(1000, 0.5, "token_id")
        self.assertEqual(len(buy_orders), 4)

        sell_orders = amm.get_sell_orders(1000, 0.5, "token_id")
        print(sell_orders)
        self.assertEqual(len(sell_orders), 4)
