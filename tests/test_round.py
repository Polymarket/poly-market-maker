import json
from unittest import TestCase
import unittest

from poly_market_maker.market import Token

MIN_TICK = 0.01


def apply_margin(x, m):
    return MIN_TICK * round((x - m) / MIN_TICK)


class TestRoundMinTick(TestCase):
    def test_round_min_tick(self):
        a = 0.58

        self.assertEqual(apply_margin(a, 0.03), 0.55)
        self.assertEqual(apply_margin(1 - a, -0.03), 0.45)

        print(round(0.58 / MIN_TICK) * MIN_TICK)
        # print(round((1 - a) - (-0.05) / MIN_TICK))
        self.assertEqual(apply_margin(a, 0.05), 0.53)

        print(1 - a)
        x = MIN_TICK * round((1 - a + 0.05) / MIN_TICK)
        print(x)
        print(x - x % MIN_TICK)
        self.assertEqual(apply_margin(1 - a, -0.05), 0.48)
