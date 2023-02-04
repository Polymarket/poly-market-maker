import json
from re import M
from unittest import TestCase, mock
from web3 import Web3
from poly_market_maker.market import Market, Token, Collateral
from poly_market_maker.strategies.amm import AMMManager


class TestAMM(TestCase):
    def test_get_orders(self):
        p = 0.5
        depth = 0.05
        p_max = depth + p
        size = 1000
        delta = 0.01
        amm_manager = AMMManager(
            token_id_a="token_id_a",
            token_id_b="token_id_b",
            p_min=0.05,
            p_max=p_max,
            delta=delta,
            depth=depth,
        )

        orders = amm_manager.get_orders(p, p, 0, 0, 1000)

        self.assertTrue(len(orders) > 0)
