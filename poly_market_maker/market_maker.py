import argparse
import json
import logging
import sys


from .gas import GasStation, GasStrategy
from .utils import math_round_down, setup_logging, setup_web3

from .band import Bands
from .order import Order
from .clob_api import ClobApi
from .constants import BUY, SELL
from .lifecycle import Lifecycle
from .orderbook import OrderBookManager

from .contracts import Contracts


class ClobMarketMakerKeeper:
    """Market maker keeper on Polymarket CLOB"""

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

        parser.add_argument("--gas-strategy", type=str, default="fixed",
                            help="Gas strategy to be used['fixed', 'station', 'web3']")

        parser.add_argument("--gas-station-url", type=str, help="Gas station url")

        parser.add_argument("--fixed-gas-price", type=int, help="Fixed gas price(gwei) to be used")

        self.args = parser.parse_args(args)
        self.web3 = setup_web3(self.args)
        self.address = self.web3.eth.account.from_key(self.args.eth_key).address

        self.bands_config = self.args.config
        self.token_id = self.args.token_id
        self.clob_api = ClobApi(self.token_id, self.args)

        self.gas_station = GasStation(
            strat=GasStrategy(self.args.gas_strategy), 
            w3=self.web3, 
            url=self.args.gas_station_url, 
            fixed=self.args.fixed_gas_price
        )
        self.contracts = Contracts(self.web3, self.gas_station) 

        self.order_book_manager = OrderBookManager(self.args.refresh_frequency, max_workers=1)
        self.order_book_manager.get_orders_with(lambda: self.clob_api.get_orders())
        self.order_book_manager.get_balances_with(lambda: self.get_balances())
        self.order_book_manager.cancel_orders_with(lambda order: self.clob_api.cancel_order(order.id))
        self.order_book_manager.cancel_all_orders_with(lambda: self.clob_api.cancel_all_orders())
        self.order_book_manager.start()

    def get_balances(self):
        """
        Fetch the onchain balances of collateral and conditional tokens for the keeper
        """
        self.logger.debug(f"Getting balances for address: {self.address}")
        collateral_balance = self.contracts.token_balance_of(self.clob_api.get_collateral_address(), self.address)
        conditional_balance = self.contracts.token_balance_of(self.clob_api.get_conditional_address(), self.address, self.token_id)
        return {"collateral": collateral_balance, "conditional": conditional_balance}

    def approve(self):
        """
        Approve the keeper on the collateral and conditional tokens
        """
        collateral = self.clob_api.get_collateral_address()
        conditional = self.clob_api.get_conditional_address()
        exchange = self.clob_api.get_exchange()
        executor = self.clob_api.get_executor()
                
        self.contracts.max_approve_erc20(collateral, self.address, exchange)
        self.contracts.max_approve_erc20(collateral, self.address, executor)

        self.contracts.max_approve_erc1155(conditional, self.address, exchange)
        self.contracts.max_approve_erc1155(conditional, self.address, executor)


    def main(self):
        with Lifecycle() as lifecycle:
            lifecycle.initial_delay(5) # 5 second initial delay so that bg threads fetch the orderbook
            lifecycle.on_startup(self.startup)
            lifecycle.every(3, self.synchronize) # Sync every 3s
            lifecycle.on_shutdown(self.shutdown)

    def startup(self):
        self.logger.info("Running startup callback...")
        self.approve()
        self.logger.info("Startup complete!")

    def synchronize(self):
        """
        Synchronize the orderbook by cancelling orders out of bands and placing new orders if necessary
        """
        self.logger.debug("Synchronizing orderbook...")
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
            self.logger.debug("Order book sync is in progress, not placing new orders")
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

        # Create new orders if needed
        new_orders = bands.new_orders(our_buy_orders=buys,
                                           our_sell_orders=sells,
                                           our_buy_balance=free_buy_balance,
                                           our_sell_balance=free_sell_balance,
                                           target_price=target_price)
        
        if len(new_orders) > 0:
            self.logger.info(f"About to place {len(new_orders)} new orders!")
            self.place_orders(new_orders)
        
        self.logger.debug("Synchronized orderbook!")

    def place_orders(self, new_orders):
        """
        Place new orders
        :param new_orders: list[Orders] 
        """
        def place_order_function(new_order_to_be_placed):
            price = math_round_down(new_order_to_be_placed.price, 2)
            size = new_order_to_be_placed.size
            side= new_order_to_be_placed.side
            order_id = self.clob_api.place_order(price=price, size=size, side=side)
            return Order(price=price, size=size, side=side, id=order_id)

        for new_order in new_orders:
            self.order_book_manager.place_order(lambda new_order=new_order: place_order_function(new_order))

    def shutdown(self):
        """
        Shut down the keeper
        """
        self.logger.info("Keeper shutting down...")
        self.order_book_manager.cancel_all_orders()
        self.logger.info("Keeper is shut down!")


if __name__ == '__main__':
    setup_logging()
    ClobMarketMakerKeeper(sys.argv[1:]).main()
