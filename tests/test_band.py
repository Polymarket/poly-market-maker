import json
from unittest import TestCase
import unittest

from poly_market_maker.band import BuyBand, Bands
from poly_market_maker.constants import BUY, SELL
from poly_market_maker.order import Order

class TestBand(TestCase):

    @unittest.skip
    def test_create_band(self):

        test_band = BuyBand({
            "minMargin": 0.005,
            "avgMargin": 0.01,
            "maxMargin": 0.02,
            "minAmount": 20.0,
            "avgAmount": 30.0,
            "maxAmount": 40.0
        })

        self.assertEqual(test_band.min_margin, 0.005)
        self.assertEqual(test_band.avg_margin, 0.01)
        self.assertEqual(test_band.max_margin, 0.02)
        self.assertEqual(test_band.min_amount, 20.0)
        self.assertEqual(test_band.avg_amount, 30.0)
        self.assertEqual(test_band.max_amount, 40.0)

    @unittest.skip
    def test_excessive_orders(self):
        # Given the below buy band with a target_price of fifty cents
        # meaning we should have orders at least minMargin away from the target_price
        # and at most maxMargin away from the target_price
        # Band is from {0.495 : 0.40 }
        test_band = BuyBand({
            "minMargin": 0.01,
            "avgMargin": 0.10,
            "maxMargin": 0.20,
            "minAmount": 1.0,
            "avgAmount": 10.0,
            "maxAmount": 50.0
        })
        orders = [
            Order(size=10, price=0.48, side="buy"),
            Order(size=20, price=0.45, side="buy"), 
            Order(size=30, price=0.42, side="buy"), 
        ]

        # with a target_price of fifty cents
        target_price = 0.50

        # with no orders, nothing gets canceled
        self.assertEqual(len(test_band.excessive_orders([], target_price, True, True)), 0)

        # Total order size > maxAmount so we need to cancel some orders
        # since there is only 1 band, we cancel orders closest to the target price as those are the most "at risk"
        scheduled_to_be_canceled = test_band.excessive_orders(orders, target_price, True, True)
        self.assertEqual(len(scheduled_to_be_canceled), 1)
        self.assertEqual(scheduled_to_be_canceled.pop(), orders[0])

        # If there were multiple bands, we'd cancel orders furthest from the target price, as those are least likely to get hit
        scheduled_to_be_canceled = test_band.excessive_orders(orders, target_price, False, True)
        self.assertEqual(len(scheduled_to_be_canceled), 1)
        self.assertEqual(scheduled_to_be_canceled.pop(), orders[2])

    @unittest.skip
    def test_create_bands(self):
        with open("./bands.json") as fh:
            test_bands = Bands.read(json.load(fh))

        self.assertIsNotNone(test_bands)
        self.assertEqual(len(test_bands.buy_bands), 2)
        self.assertEqual(len(test_bands.sell_bands), 2)

    @unittest.skip
    def test_bands_cancellable_orders(self):
        with open("./tests/bands.json") as fh:
            test_bands = Bands.read(json.load(fh))
        
        # Initialize buys and sells that fit in both bands
        target_price = 0.50
        buys = [Order(size=20, price=0.45, side=BUY), Order(size=30, price=0.39, side=BUY)]
        sells = [Order(size=20, price=0.55, side=SELL), Order(size=30, price=0.65, side=SELL)]

        # Expect none to be cancelled
        self.assertEqual(len(test_bands.cancellable_orders(buys, sells, target_price)), 0)

        # Say price moves to 80c
        target_price = 0.80

        # All 4 orders are now cancellable
        self.assertEqual(len(test_bands.cancellable_orders(buys, sells, target_price)), 4)

    
    def test_bands_new_orders(self):
        with open("./tests/bands.json") as fh:
            test_bands = Bands.read(json.load(fh))
        
        # Given the following balances:
        target_price = 0.5
        keeper_usdc_balance = 100.0
        keeper_yes_balance  = 100.0

        # and the following existing orders:
        existing_buys = [Order(size=5, price=0.45, side=BUY)]
        existing_sells = [Order(size=5, price=0.55, side=BUY)]

        # place new orders
        new_orders = test_bands.new_orders(existing_buys, existing_sells, keeper_usdc_balance, keeper_yes_balance, target_price)
        new_buys = [ o for o in new_orders if o.side==BUY]
        new_sells = [ o for o in new_orders if o.side==SELL]

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
        # price = target_price - (1 - avgMargin) = 0.5 * (1 - 0.25) = 0.375
        self.assertEqual(new_buys[1].size, 30.0)
        self.assertEqual(new_buys[1].price, 0.375)

        # Similarly for sells
        self.assertEqual(new_sells[0].size, 15.0)
        self.assertEqual(new_sells[0].price, 0.55)

        self.assertEqual(new_sells[1].size, 30.0)
        self.assertEqual(new_sells[1].price, 0.625)
        



