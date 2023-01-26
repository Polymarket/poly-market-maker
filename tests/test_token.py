import json
from unittest import TestCase
import unittest

from poly_market_maker.market import Token


class TestToken(TestCase):
    def test_token(self):
        self.assertEqual(Token.A.value, "tokenA")
        self.assertEqual(Token.B.value, "tokenB")

    def test_complement(self):
        self.assertEqual(Token.A.complement(), Token.B)
        self.assertEqual(Token.B.complement(), Token.A)
