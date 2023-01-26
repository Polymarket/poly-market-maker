import json
from unittest import TestCase
import unittest

from poly_market_maker.order import BUY, SELL

buy = "buy"
sell = "sell"


class TestToken(TestCase):
    def test_sides(self):
        self.assertEqual(BUY, buy)
        self.assertEqual(SELL, sell)
