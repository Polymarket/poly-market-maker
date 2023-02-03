import json
from re import M
from unittest import TestCase, mock
from web3 import Web3
from poly_market_maker.market import Market, Token, Collateral
from poly_market_maker.strategies.amm_strategy import AMMStrategy


class PriceFeed:
    def __init__(self):
        self.price = 0.7

    def get_price(self, token_id):
        return 0.71

    def set_price(self, price):
        self.price = price


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
        self.order_book.orders_being_placed = orders

    def cancel_orders(self, orders):
        self.order_book.orders_being_cancelled = orders

    def update_orders(self):
        self.order_book.orders = list(
            set(self.order_book.orders)
            .union(set(self.order_book.orders_being_placed))
            .difference(set(self.order_book.orders_being_cancelled))
        )
        self.order_book.orders_being_placed = []
        self.order_book.orders_being_cancelled = []


class TestAMMStrategy(TestCase):
    def test_synchronize(self):
        price_feed = PriceFeed()
        order_book_manager = OrderBookManager()
        market = Market("condition_id", "token_id_a", "token_id_b")
        strategy = AMMStrategy(price_feed, market, order_book_manager)

        strategy.synchronize()
        order_book = order_book_manager.get_order_book()

        len_orders_being_placed = len(order_book.orders_being_placed)
        self.assertTrue(len_orders_being_placed > 0)
        self.assertTrue(len(order_book.orders_being_cancelled) == 0)

        order_book_manager.update_orders()
        self.assertTrue(len(order_book.orders_being_placed) == 0)
        self.assertTrue(len(order_book.orders) == len_orders_being_placed)

        price_feed.set_price(0.4)
        strategy.synchronize()
        self.assertTrue(len(order_book.orders_being_placed) == 0)
        self.assertTrue(
            len(order_book.orders_being_cancelled) == len_orders_being_placed
        )
        self.assertTrue(len(order_book.orders) == len_orders_being_placed)

        order_book_manager.update_orders()
        strategy.synchronize()
        self.assertTrue(len(order_book.orders) == 0)
        self.assertTrue(len(order_book.orders_being_placed) > 0)
        self.assertTrue(len(order_book.orders_being_cancelled) == 0)
