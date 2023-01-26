import json
from unittest import TestCase
import unittest

from poly_market_maker.market import Market, Token

condition_id = "conditionId"
token_id_a = "tokenIdA"
token_id_b = "tokenIdB"


class TestMarket(TestCase):
    market = Market(condition_id, token_id_a, token_id_b)

    def test_init_market(self):
        self.assertEqual(self.market.condition_id, condition_id)
        self.assertEqual(self.market.token_id_A, token_id_a)
        self.assertEqual(self.market.token_id_B, token_id_b)

    def test_token_id(self):
        self.assertEqual(self.market.token_id(Token.A), token_id_a)
        self.assertEqual(self.market.token_id(Token.B), token_id_b)

    def test_token(self):
        self.assertEqual(self.market.token(token_id_a), Token.A)
        self.assertEqual(self.market.token(token_id_b), Token.B)
