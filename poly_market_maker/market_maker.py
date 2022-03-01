import argparse
import json
import logging
import sys

from web3 import Web3

from .band import Bands
from .order import Order
from .clob_api import ClobApi
from .constants import BUY, SELL
from .lifecycle import Lifecycle
from .orderbook import OrderBookManager
from .token_utils import token_balance_of


class ClobMarketMakerKeeper:
    """Market maker keeper on Polymarket CLOB"""

    logging.basicConfig(format='%(asctime)-15s %(levelname)-8s %(message)s',
                        level=(logging.DEBUG))
    logger = logging.getLogger(__name__)

    def __init__(self, args: list, **kwargs):
        parser = argparse.ArgumentParser(prog='poly-market-maker')

        parser.add_argument("--eth-key", type=str, required=True, help="Private key")

        parser.add_argument("--chain-id", type=int, required=True, help="Chain ID")

        parser.add_argument("--rpc-url", type=str, required=True, help="RPC URL")

        parser.add_argument("--clob-api-url", type=str, required=True, help="CLOB API url")

        parser.add_argument("--clob-api-key", type=str, required=True, help="CLOB API Key")

        parser.add_argument("--clob-api-secret", type=str, required=True, help="CLOB API secret")

        parser.add_argument("--clob-api-passphrase", type=str, required=True, help="CLOB API passphrase")

        parser.add_argument("--config", type=str, required=True, help="Bands configuration file")

        parser.add_argument("--token-id", type=int, required=True, help="The token_id of the market being made")

        parser.add_argument("--refresh-frequency", type=int, default=3,
                            help="Order book refresh frequency (in seconds, default: 3)")

        self.args = parser.parse_args(args)
        self.web3 = Web3(Web3.HTTPProvider(self.args.rpc_url))
        self.bands_config = self.args.config
        self.token_id = self.args.token_id
        self.clob_api = ClobApi(self.token_id, self.args)

        self.order_book_manager = OrderBookManager(self.args.refresh_frequency, max_workers=1)
        self.order_book_manager.get_orders_with(lambda: self.clob_api.get_orders())
        self.order_book_manager.get_balances_with(lambda: self.get_balances())
        self.order_book_manager.cancel_orders_with(lambda order: self.clob_api.cancel_order(order.id))
        self.order_book_manager.cancel_all_orders_with(lambda _: self.clob_api.cancel_all_orders())
        self.order_book_manager.start()

    def get_balances(self):
        keeper_address = self.clob_api.get_address()
        self.logger.info(f"Getting balances for address: {keeper_address}")
        collateral_balance = token_balance_of(self.web3, self.clob_api.get_collateral_address(), keeper_address)
        conditional_balance = token_balance_of(self.web3, self.clob_api.get_conditional_address(), keeper_address, self.token_id)
        return {"collateral": collateral_balance, "conditional": conditional_balance}

    def main(self):
        with Lifecycle() as lifecycle:
            lifecycle.initial_delay(5)
            lifecycle.on_startup(self.startup)
            lifecycle.every(3, self.synchronize)
            lifecycle.on_shutdown(self.shutdown)

    def startup(self):
        self.logger.info("Running startup callback...")
        pass

    def synchronize(self):
        self.logger.info("Synchronizing orderbook...")
        with open(self.bands_config) as fh:
            bands = Bands.read(json.load(fh))
        
        orderbook = self.order_book_manager.get_order_book()
        #fetch target price from CLOB API via REST
        #TODO: switch to wss
        target_price = self.clob_api.get_price()

        # Cancel orders
        buys = [o for o in orderbook.orders if o.side == BUY]
        sells = [o for o in orderbook.orders if o.side == SELL]

        cancellable_orders = bands.cancellable_orders(our_buy_orders=buys,
                                                      our_sell_orders=sells,
                                                      target_price=target_price)
        if len(cancellable_orders) > 0:
            self.order_book_manager.cancel_orders(cancellable_orders)
            return

        # Do not place new orders if order book state is not confirmed
        if orderbook.orders_being_placed or orderbook.orders_being_cancelled:
            self.logger.debug("Order book is in progress, not placing new orders")
            return

        if orderbook.balances.get("collateral") is None or orderbook.balances.get("conditional") is None:
            self.logger.debug("Balances invalid/non-existent")
            return

        balance_locked_by_open_buys = sum(o.size * o.price for o in buys)
        balance_locked_by_open_sells = sum(o.size for o in sells)
        self.logger.debug(f"Collateral locked by buys: {balance_locked_by_open_buys}")
        self.logger.debug(f"Conditional locked by sells: {balance_locked_by_open_sells}")

        free_buy_balance = orderbook.balances.get("collateral") - balance_locked_by_open_buys
        free_sell_balance = orderbook.balances.get("conditional") - balance_locked_by_open_sells

        self.logger.debug(f"Free buy balance: {free_buy_balance}")
        self.logger.debug(f"Free sell balance: {free_sell_balance}")

        # Place new orders
        new_orders = bands.new_orders(our_buy_orders=buys,
                                           our_sell_orders=sells,
                                           our_buy_balance=free_buy_balance,
                                           our_sell_balance=free_sell_balance,
                                           target_price=target_price)
        self.logger.info(f"New orders ready to be placed: {len(new_orders)}")
        self.place_orders(new_orders)
        
        self.logger.info("Synchronized orderbook!")

    def place_orders(self, new_orders):
        """
        """
        self.logger.info("Running place_orders callback...")
        def place_order_function(new_order_to_be_placed):
            # TODO: get min tick from clob_api
            # hardcoding 2 decimal places
            price = round(new_order_to_be_placed.price, 2) 
            size = round(new_order_to_be_placed.size, 2)
            side= new_order_to_be_placed.side
            order_id = self.clob_api.place_order(price=price, size=size, side=side)
            return Order(price=price, size=size, side=side, id=order_id)

        for new_order in new_orders:
            self.order_book_manager.place_order(lambda new_order=new_order: place_order_function(new_order))

    def shutdown(self):
        """
        """
        self.logger.info("Running shutdown callback...")
        # self.order_book_manager.cancel_all_orders()


if __name__ == '__main__':
    ClobMarketMakerKeeper(sys.argv[1:]).main()
