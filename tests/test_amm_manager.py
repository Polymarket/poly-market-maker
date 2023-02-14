from unittest import TestCase

from poly_market_maker.strategies.amm import AMMManager
from poly_market_maker.order import Side
from poly_market_maker.token import Token


class TestAMM(TestCase):
    def test_get_expected_order_prices(self):
        p = 0.5
        depth = 0.05
        p_min = 0.05
        p_max = 0.95
        delta = 0.01
        spread = 0.02

        amm_manager = AMMManager(
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

        sell_orders_a = [order for order in sell_orders if order.token == Token.A]
        sell_orders_b = [order for order in sell_orders if order.token == Token.B]
        buy_orders_a = [order for order in buy_orders if order.token == Token.A]
        buy_orders_b = [order for order in buy_orders if order.token == Token.B]

        sell_prices_a = [order.price for order in sell_orders_a]
        self.assertEqual(sell_prices_a, [0.52, 0.53, 0.54, 0.55, 0.56, 0.57])
        sell_prices_b = [order.price for order in sell_orders_b]
        self.assertEqual(sell_prices_b, [0.52, 0.53, 0.54, 0.55, 0.56, 0.57])

        buy_prices_a = [order.price for order in buy_orders_a]
        self.assertEqual(buy_prices_a, [0.48, 0.47, 0.46, 0.45, 0.44, 0.43])
        buy_prices_b = [order.price for order in buy_orders_b]
        self.assertEqual(buy_prices_b, [0.48, 0.47, 0.46, 0.45, 0.44, 0.43])

    def test_get_expected_order_sizes(self):
        p = 0.5
        depth = 0.05
        p_min = 0.05
        p_max = 0.95
        delta = 0.01
        spread = 0.01

        amm_manager = AMMManager(
            p_min=p_min,
            p_max=p_max,
            delta=delta,
            depth=depth,
            spread=spread,
        )

        x_a = 1000
        x_b = 1000
        y = 2000

        orders = amm_manager.get_expected_orders(p, p, x_a, x_b, y)

        sell_orders = [order for order in orders if order.side == Side.SELL]
        buy_orders = [order for order in orders if order.side == Side.BUY]

        sell_orders_a = [order for order in sell_orders if order.token == Token.A]
        sell_orders_b = [order for order in sell_orders if order.token == Token.B]
        buy_orders_a = [order for order in buy_orders if order.token == Token.A]
        buy_orders_b = [order for order in buy_orders if order.token == Token.B]

        sell_sizes_a = [order.size for order in sell_orders_a]
        for i in range(len(sell_sizes_a) - 1):
            self.assertGreater(sell_sizes_a[i], sell_sizes_a[i + 1])

        self.assertLessEqual(sum(sell_sizes_a), x_a)

        sell_sizes_b = [order.size for order in sell_orders_b]
        for i in range(len(sell_sizes_b) - 1):
            self.assertGreater(sell_sizes_b[i], sell_sizes_b[i + 1])

        self.assertLessEqual(sum(sell_sizes_b), x_b)

        buy_sizes_a = [order.size for order in buy_orders_a]
        for i in range(len(buy_sizes_a) - 1):
            self.assertLess(buy_sizes_a[i], buy_sizes_a[i + 1])

        net_cost_a = sum(order.price * order.size for order in buy_orders_a)
        net_cost_b = sum(order.price * order.size for order in buy_orders_b)
        self.assertLessEqual(net_cost_a + net_cost_b, y)

    def test_get_expected_orders(self):
        y = 9889.901666
        x_a = 2026.350247
        x_b = 6123.364332

        p_a = 0.45
        p_b = 0.55

        depth = 0.05
        p_min = 0.05
        p_max = 0.95
        delta = 0.01
        spread = 0.01

        amm_manager = AMMManager(
            p_min=p_min,
            p_max=p_max,
            delta=delta,
            depth=depth,
            spread=spread,
        )

        expected_orders = amm_manager.get_expected_orders(p_a, p_b, x_a, x_b, y)
