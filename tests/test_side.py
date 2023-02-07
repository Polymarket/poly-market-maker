import json
from unittest import TestCase
import unittest

from poly_market_maker.order import Side
from py_clob_client.order_builder.constants import BUY, SELL


class TestSide(TestCase):
    def test_side(self):
        self.assertEqual(Side.BUY.value, BUY)
        self.assertEqual(Side.SELL.value, SELL)

    def test_side_from_string(self):
        self.assertEqual(Side("buy"), Side.BUY)
        self.assertEqual(Side("Buy"), Side.BUY)
        self.assertEqual(Side("BUY"), Side.BUY)

        self.assertEqual(Side("sell"), Side.SELL)
        self.assertEqual(Side("Sell"), Side.SELL)
        self.assertEqual(Side("SELL"), Side.SELL)

        self.assertRaises(ValueError, Side, "sel")
        self.assertRaises(ValueError, Side, "buyy")
