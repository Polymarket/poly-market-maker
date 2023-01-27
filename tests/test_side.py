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
        self.assertEqual(Side.from_string("buy"), Side.BUY)
        self.assertEqual(Side.from_string("Buy"), Side.BUY)
        self.assertEqual(Side.from_string("BUY"), Side.BUY)

        self.assertEqual(Side.from_string("sell"), Side.SELL)
        self.assertEqual(Side.from_string("Sell"), Side.SELL)
        self.assertEqual(Side.from_string("SELL"), Side.SELL)

        self.assertRaises(ValueError, Side.from_string, "sel")
        self.assertRaises(ValueError, Side.from_string, "buyy")
