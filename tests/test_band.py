import json
from unittest import TestCase
import unittest

from poly_market_maker.band import BuyBand, Bands
from poly_market_maker.constants import BUY, SELL
from poly_market_maker.order import Order


class TestBand(TestCase):
    def test_create_band(self):

        test_band = BuyBand(
            {
                "minMargin": 0.005,
                "avgMargin": 0.01,
                "maxMargin": 0.02,
                "minAmount": 20.0,
                "avgAmount": 30.0,
                "maxAmount": 40.0,
            }
        )

        self.assertEqual(test_band.min_margin, 0.005)
        self.assertEqual(test_band.avg_margin, 0.01)
        self.assertEqual(test_band.max_margin, 0.02)
        self.assertEqual(test_band.min_amount, 20.0)
        self.assertEqual(test_band.avg_amount, 30.0)
        self.assertEqual(test_band.max_amount, 40.0)

    def test_excessive_orders(self):
        # Given the below buy band with a target_price of 0.5
        # meaning we should have orders at least minMargin away from the target_price
        # and at most maxMargin away from the target_price
        # Band is from {0.495 : 0.40 }
        test_band = BuyBand(
            {
                "minMargin": 0.01,
                "avgMargin": 0.10,
                "maxMargin": 0.20,
                "minAmount": 1.0,
                "avgAmount": 10.0,
                "maxAmount": 50.0,
            }
        )
        orders = [
            Order(size=10, price=0.48, side="buy"),
            Order(size=20, price=0.45, side="buy"),
            Order(size=30, price=0.42, side="buy"),
        ]

        # with a target_price of fifty cents
        target_price = 0.50

        # with no orders, nothing gets canceled
        self.assertEqual(
            len(test_band.excessive_orders([], target_price, True, True)), 0
        )

        # Total order size > maxAmount so we need to cancel some orders
        # since there is only 1 band, we cancel orders closest to the target price as those are the most "at risk"
        scheduled_to_be_canceled = test_band.excessive_orders(
            orders, target_price, True, True
        )
        self.assertEqual(len(scheduled_to_be_canceled), 1)
        self.assertEqual(scheduled_to_be_canceled.pop(), orders[0])

        # If there were multiple bands, we'd cancel orders furthest from the target price, as those are least likely to get hit
        scheduled_to_be_canceled = test_band.excessive_orders(
            orders, target_price, False, True
        )
        self.assertEqual(len(scheduled_to_be_canceled), 1)
        self.assertEqual(scheduled_to_be_canceled.pop(), orders[2])

    def test_create_bands(self):
        with open("./tests/bands.json") as fh:
            test_bands = Bands.read(json.load(fh))

        self.assertIsNotNone(test_bands)
        self.assertEqual(len(test_bands.buy_bands), 2)
        self.assertEqual(len(test_bands.sell_bands), 2)

    def test_bands_cancellable_orders(self):
        with open("./tests/bands.json") as fh:
            test_bands = Bands.read(json.load(fh))

        # Initialize buys and sells that fit in both bands
        target_price = 0.50
        buys = [
            Order(size=20, price=0.45, side=BUY),
            Order(size=30, price=0.39, side=BUY),
        ]
        sells = [
            Order(size=20, price=0.55, side=SELL),
            Order(size=30, price=0.65, side=SELL),
        ]

        # Expect none to be cancelled
        self.assertEqual(
            len(test_bands.cancellable_orders(buys, sells, target_price)), 0
        )

        # Say price moves to 80c
        target_price = 0.80

        # All 4 orders are now cancellable
        self.assertEqual(
            len(test_bands.cancellable_orders(buys, sells, target_price)), 4
        )

    def test_bands_new_orders(self):
        with open("./tests/bands.json") as fh:
            test_bands = Bands.read(json.load(fh))

        # Given the following balances:
        target_price = 0.5
        keeper_usdc_balance = 100.0
        keeper_yes_balance = 100.0

        # and the following existing orders:
        existing_buys = [Order(size=5, price=0.45, side=BUY)]
        existing_sells = [Order(size=5, price=0.55, side=SELL)]

        # place new orders
        new_orders = test_bands.new_orders(
            existing_buys,
            existing_sells,
            keeper_usdc_balance,
            keeper_yes_balance,
            target_price,
        )
        new_buys = [o for o in new_orders if o.side == BUY]
        new_sells = [o for o in new_orders if o.side == SELL]

        # For BuyBand1 = Band[type=buy, spread<0.01, 0.2>, amount<10.0, 50.0>]
        # the existing buy has a size 5, failing the minAmount 10 requirement
        # so we expect to have created a new buy with:
        # size = avgAmount - existingSize = 20.0 - 5 = 15.0
        # price = target_price - (1 - avgMargin) = 0.5 * (1 - 0.1) = 0.45
        self.assertEqual(new_buys[0].size, 15.0)
        self.assertEqual(new_buys[0].price, 0.45)

        # For BuyBand2 = Band[type=buy, spread<0.2, 0.4>, amount<20.0, 40.0>]
        # we have no buys in that band, failing the minAmount 20 requirement
        # new buy:
        # size = avgAmount - existingAmount = 30 - 0
        # price = target_price - (1 - avgMargin) = 0.5 * (1 - 0.25) = buys are rounded down(0.375, 2) == 0.37
        self.assertEqual(new_buys[1].size, 30.0)
        self.assertEqual(new_buys[1].price, 0.37)

        # Similarly for sells
        self.assertEqual(new_sells[0].size, 15.0)
        self.assertEqual(new_sells[0].price, 0.55)

        self.assertEqual(new_sells[1].size, 30.0)
        self.assertEqual(new_sells[1].price, 0.63)  # asks are rounded up

    def test_virtual_bands_orders(self):
        # load bands with margins that are very close together 
        # without adjustment all orders would be at same price
        with open("./tests/tight_bands.json") as fh:
            test_bands = Bands.read(json.load(fh))

        target_price = .50

        # confirm adjustments are made to spread orders to neighboring ticks
        virtual_sell_bands = test_bands._calculate_virtual_sell_bands(target_price)
        
        self.assertEqual(virtual_sell_bands[0].min_margin, .02)
        self.assertEqual(virtual_sell_bands[0].avg_margin, .02)
        self.assertEqual(virtual_sell_bands[0].max_margin, .04)

        self.assertEqual(virtual_sell_bands[1].min_margin, .04)
        self.assertEqual(virtual_sell_bands[1].avg_margin, .04)
        self.assertEqual(virtual_sell_bands[1].max_margin, .06)

        self.assertEqual(virtual_sell_bands[2].min_margin, .06)
        self.assertEqual(virtual_sell_bands[2].avg_margin, .06)
        self.assertEqual(virtual_sell_bands[2].max_margin, .08)

        # confirm adjustments are made to spread orders to neighboring ticks
        virtual_buy_bands = test_bands._calculate_virtual_buy_bands(target_price)

        self.assertEqual(virtual_buy_bands[0].min_margin, .02)
        self.assertEqual(virtual_buy_bands[0].avg_margin, .02)
        self.assertEqual(virtual_buy_bands[0].max_margin, .04)

        self.assertEqual(virtual_buy_bands[1].min_margin, .04)
        self.assertEqual(virtual_buy_bands[1].avg_margin, .04)
        self.assertEqual(virtual_buy_bands[1].max_margin, .06)

        self.assertEqual(virtual_buy_bands[2].min_margin, .06)
        self.assertEqual(virtual_buy_bands[2].avg_margin, .06)
        self.assertEqual(virtual_buy_bands[2].max_margin, .08)

        target_price = .80

        # confirm adjustments are made to spread orders to neighboring ticks
        virtual_sell_bands = test_bands._calculate_virtual_sell_bands(target_price)

        self.assertEqual(virtual_sell_bands[0].min_margin, .0125)
        self.assertEqual(virtual_sell_bands[0].avg_margin, .0125)
        self.assertEqual(virtual_sell_bands[0].max_margin, .025)

        self.assertEqual(virtual_sell_bands[1].min_margin, .025)
        self.assertEqual(virtual_sell_bands[1].avg_margin, .025)
        self.assertEqual(virtual_sell_bands[1].max_margin, .0375)

        self.assertEqual(virtual_sell_bands[2].min_margin, .0375)
        self.assertEqual(virtual_sell_bands[2].avg_margin, .0375)
        self.assertEqual(virtual_sell_bands[2].max_margin, .05)

        target_price = .20

        # confirm adjustments are made to spread orders to neighboring ticks
        virtual_buy_bands = test_bands._calculate_virtual_buy_bands(target_price)

        self.assertEqual(virtual_buy_bands[0].min_margin, .05)
        self.assertEqual(virtual_buy_bands[0].avg_margin, .05)
        self.assertEqual(virtual_buy_bands[0].max_margin, .1)

        self.assertEqual(virtual_buy_bands[1].min_margin, .1)
        self.assertEqual(virtual_buy_bands[1].avg_margin, .1)
        self.assertEqual(virtual_buy_bands[1].max_margin, .15)

        self.assertEqual(virtual_buy_bands[2].min_margin, .15)
        self.assertEqual(virtual_buy_bands[2].avg_margin, .15)
        self.assertEqual(virtual_buy_bands[2].max_margin, .2)

    def test_tight_bands_cancellable_and_new_orders(self):
        with open("./tests/tight_bands.json") as fh:
            test_bands = Bands.read(json.load(fh))

        # Initialize buys and sells that fit in two of 3 adjusted bands on each side
        target_price = 0.50
        buys = [
            Order(size=100, price=0.49, side=BUY),
            Order(size=100, price=0.48, side=BUY),
        ]
        sells = [
            Order(size=100, price=0.51, side=SELL),
            Order(size=100, price=0.52, side=SELL),
        ]

        # Expect none to be cancelled
        self.assertEqual(
            len(test_bands.cancellable_orders(buys, sells, target_price)), 0
        )

        # Expect two to need to be created
        keeper_usdc_balance = 500.0
        keeper_yes_balance = 500.0

        new_orders = test_bands.new_orders(
            buys,
            sells,
            keeper_usdc_balance,
            keeper_yes_balance,
            target_price,
        )

        self.assertEqual(len(new_orders), 2)

        self.assertEqual(new_orders[0].price, .47)
        self.assertEqual(new_orders[0].side, BUY)

        self.assertEqual(new_orders[1].price, .53)
        self.assertEqual(new_orders[1].side, SELL)


        # Say price moves to 80c
        target_price = 0.80

        # All 4 orders are now cancellable
        self.assertEqual(
            len(test_bands.cancellable_orders(buys, sells, target_price)), 4
        )

        # Expect six to need to be created
        new_orders = test_bands.new_orders(
            [],
            [],
            keeper_usdc_balance,
            keeper_yes_balance,
            target_price,
        )

        self.assertEqual(len(new_orders), 6)

        self.assertEqual(new_orders[0].price, .79)
        self.assertEqual(new_orders[0].side, BUY)

        self.assertEqual(new_orders[1].price, .78)
        self.assertEqual(new_orders[1].side, BUY)

        self.assertEqual(new_orders[2].price, .77)
        self.assertEqual(new_orders[2].side, BUY)

        self.assertEqual(new_orders[3].price, .81)
        self.assertEqual(new_orders[3].side, SELL)

        self.assertEqual(new_orders[4].price, .82)
        self.assertEqual(new_orders[4].side, SELL)

        self.assertEqual(new_orders[5].price, .83)
        self.assertEqual(new_orders[5].side, SELL)

    def test_cant_create_order_over_dollar_or_under_zero(self):
        with open("./tests/tight_bands.json") as fh:
            test_bands = Bands.read(json.load(fh))
        
        target_price = 1.0
        new_asks = test_bands._new_sell_orders([], 500.0, target_price)

        # shouldn't be any valid asks because they would all be over 1.0
        self.assertEqual(len(new_asks), 0)

        target_price = 0.0
        new_asks = test_bands._new_buy_orders([], 500.0, target_price)

        # shouldn't be any valid bids because they would all be under 0.0
        self.assertEqual(len(new_asks), 0)


