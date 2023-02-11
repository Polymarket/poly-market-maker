import json
from re import M
from unittest import TestCase, mock
from web3 import Web3
from poly_market_maker.market import Market, Token, Collateral
from poly_market_maker.strategies.amm_strategy import AMMStrategy
from poly_market_maker.order import Order, Side
import uuid


class PriceFeed:
    def __init__(self, price_a: float, price_b, market: Market):
        self.price_a = price_a
        self.price_b = price_b
        self.token_id_a = market.token_id(Token.A)
        self.token_id_b = market.token_id(Token.B)

    def get_price(self, token_id):
        match token_id:
            case self.token_id_a:
                return self.price_a
            case self.token_id_b:
                return self.price_b

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
        for order in orders:
            self.order_book.orders_being_placed += [
                Order(
                    size=order.size,
                    price=order.price,
                    token_id=order.token_id,
                    side=order.side,
                    id=uuid.uuid4(),
                )
            ]

    def cancel_orders(self, orders):
        self.order_book.orders_being_cancelled = orders

    def cancel_all_orders(self):
        self.order_book.orders_being_cancelled = [
            order for order in self.order_book.orders
        ]

    def update_orders(self):
        self.order_book.orders = list(
            set(self.order_book.orders)
            .union(set(self.order_book.orders_being_placed))
            .difference(set(self.order_book.orders_being_cancelled))
        )
        self.order_book.orders_being_placed = []
        self.order_book.orders_being_cancelled = []


class TestAMMStrategy(TestCase):
    token_id = "123"
    market = Market("9999", token_id, "456")
    config = {
        "p_min": 0.05,
        "p_max": 0.95,
        "delta": 0.01,
        "spread": 0.02,
        "depth": 0.10,
    }

    def test_synchronize(self):
        price_feed = PriceFeed(0.6, 0.4, self.market)
        order_book_manager = OrderBookManager()
        strategy = AMMStrategy(price_feed, self.market, order_book_manager, self.config)

        strategy.synchronize()
        order_book = order_book_manager.get_order_book()

        len_orders_being_placed = len(order_book.orders_being_placed)
        self.assertTrue(len_orders_being_placed > 0)
        self.assertTrue(len(order_book.orders_being_cancelled) == 0)

    def test_get_orders_to_cancel(self):
        price_feed = PriceFeed(0.6, 0.4, self.market)
        order_book_manager = OrderBookManager()
        strategy = AMMStrategy(price_feed, self.market, order_book_manager, self.config)

        expected_orders = []
        orders_to_cancel = strategy.get_orders_to_cancel(
            order_book_manager.get_order_book(), []
        )
        self.assertEqual(orders_to_cancel, [])

        open_orders = [
            Order(token_id=self.token_id, price=0.1, size=100, side=Side.BUY)
        ]
        order_book_manager.place_orders(open_orders)
        order_book_manager.update_orders()

        orders_to_cancel = strategy.get_orders_to_cancel(
            order_book_manager.get_order_book(), expected_orders
        )
        self.assertEqual(len(orders_to_cancel), len(open_orders))

        expected_orders = [
            Order(token_id=self.token_id, price=0.1, size=100, side=Side.BUY)
        ]
        orders_to_cancel = strategy.get_orders_to_cancel(
            order_book_manager.get_order_book(), expected_orders
        )
        self.assertEqual(len(orders_to_cancel), 0)

        expected_orders = [
            Order(token_id=self.token_id, price=0.1, size=50, side=Side.BUY)
        ]
        orders_to_cancel = strategy.get_orders_to_cancel(
            order_book_manager.get_order_book(), expected_orders
        )
        self.assertEqual(len(orders_to_cancel), len(open_orders))

        order_book_manager.cancel_all_orders()
        order_book_manager.update_orders()

        order_book_manager.place_orders(
            10 * [Order(token_id=self.token_id, price=0.1, size=15, side=Side.BUY)]
        )
        order_book_manager.update_orders()

        orders_to_cancel = strategy.get_orders_to_cancel(
            order_book_manager.get_order_book(), expected_orders
        )

        self.assertEqual(len(orders_to_cancel), 7)
