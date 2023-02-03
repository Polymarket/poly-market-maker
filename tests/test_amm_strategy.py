import json
from re import M
from unittest import TestCase, mock
from web3 import Web3
from poly_market_maker.market import Market, Token, Collateral
from poly_market_maker.strategies.amm_strategy import AMMStrategy


class PriceFeed:
    def get_price(self, token_id):
        return 0.71


class OrderBook:
    def __init__(self):
        self.orders = []
        self.orders_being_placed = []
        self.orders_being_cancelled = []

    def balance(self, token):
        if token == Token.A:
            return 100
        if token == Token.B:
            return 200
        if token == Collateral:
            return 1000


class OrderBookManager:
    def __init__(self):
        self.order_book = OrderBook()

    def get_order_book(self):
        return self.order_book

    def place_orders(self, orders):
        print("place orders:", orders)

    def cancel_orders(self, orders):
        print("cancel orders:", orders)


class TestAMMStrategy(TestCase):
    def test_synchronize(self):
        price_feed = PriceFeed()
        order_book_manager = OrderBookManager()
        market = Market("condition_id", "token_id_a", "token_id_b")
        strategy = AMMStrategy(price_feed, market, order_book_manager)

        strategy.synchronize()

        self.assertEqual(0, 1)
