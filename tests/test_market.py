import json
from unittest import TestCase
import unittest

from poly_market_maker.market import Market, Token

condition_id = "1111"
token_id_a = "123"
token_id_b = "456"


class TestMarket(TestCase):
    market = Market(condition_id, token_id_a, token_id_b)

    def test_init_market(self):
        self.assertEqual(self.market.condition_id, condition_id)
        self.assertEqual(self.market.token_id_a, token_id_a)
        self.assertEqual(self.market.token_id_b, token_id_b)

    def test_token_id(self):
        self.assertEqual(self.market.token_id(Token.A), token_id_a)
        self.assertEqual(self.market.token_id(Token.B), token_id_b)

    def test_token(self):
        self.assertEqual(self.market.token(token_id_a), Token.A)
        self.assertEqual(self.market.token(token_id_b), Token.B)
