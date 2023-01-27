import argparse
import json
import logging
import sys

from prometheus_client import start_http_server
from poly_market_maker.odds_api import OddsAPI
from poly_market_maker.fpmm import FPMM

from poly_market_maker.price_feed import (
    PriceFeedClob,
    PriceFeedOddsAPI,
    PriceFeedSource,
    PriceFeedFPMM,
)

from .gas import GasStation, GasStrategy
from .utils import math_round_down, setup_logging, setup_web3

from .band import Bands
from .order import Order, Side
from .market import Market, Token
from .clob_api import ClobApi
from .lifecycle import Lifecycle
from .orderbook import OrderBookManager, OrderBook
from .contracts import Contracts
from .metrics import keeper_balance_amount


class ClobMarketMakerKeeper:
    """Market maker keeper on Polymarket CLOB"""

    logger = logging.getLogger(__name__)

    def __init__(self, args: list, **kwargs):
        parser = argparse.ArgumentParser(prog="poly-market-maker")

        parser.add_argument(
            "--private-key", type=str, required=True, help="Private key"
        )

        parser.add_argument(
            "--chain-id", type=int, required=True, help="Chain ID"
        )

        parser.add_argument(
            "--rpc-url", type=str, required=True, help="RPC URL"
        )

        parser.add_argument(
            "--clob-api-url", type=str, required=True, help="CLOB API url"
        )

        parser.add_argument(
            "--clob-api-key", type=str, required=True, help="CLOB API Key"
        )

        parser.add_argument(
            "--clob-api-secret",
            type=str,
            required=True,
            help="CLOB API secret",
        )

        parser.add_argument(
            "--clob-api-passphrase",
            type=str,
            required=True,
            help="CLOB API passphrase",
        )

        parser.add_argument(
            "--bands-config",
            type=str,
            required=True,
            help="Bands configuration file",
        )

        parser.add_argument(
            "--sync-interval",
            type=int,
            required=False,
            default=30,
            help="The number of seconds in between synchronizations",
        )

        parser.add_argument(
            "--min-size",
            type=float,
            required=False,
            default=15,
            help="The minimum size of a newly placed order",
        )

        parser.add_argument(
            "--min-tick",
            type=float,
            required=False,
            default=0.01,
            help="The distance between two successive prices",
        )

        parser.add_argument(
            "--condition-id",
            type=str,
            required=True,
            help="The condition id of the market being made",
        )

        parser.add_argument(
            "--token-id-A",
            type=int,
            required=True,
            help="Either of the two token ids of the market being made",
        )
        parser.add_argument(
            "--token-id-B",
            type=int,
            required=True,
            help="The other token id of the market being made",
        )

        parser.add_argument(
            "--refresh-frequency",
            type=int,
            default=5,
            help="Order book refresh frequency (in seconds, default: 5)",
        )

        parser.add_argument(
            "--gas-strategy",
            type=str,
            default="fixed",
            help="Gas strategy to be used['fixed', 'station', 'web3']",
        )

        parser.add_argument(
            "--gas-station-url", type=str, help="Gas station url"
        )

        parser.add_argument(
            "--fixed-gas-price",
            type=int,
            help="Fixed gas price(gwei) to be used",
        )

        parser.add_argument(
            "--price-feed-source",
            type=PriceFeedSource,
            default="clob",
            help="source of the mid price of the market",
        )

        parser.add_argument("--odds-api-url", type=str, required=False)
        parser.add_argument("--odds-api-key", type=str, required=False)
        parser.add_argument("--odds-api-sport", type=str, required=False)
        parser.add_argument("--odds-api-region", type=str, required=False)
        parser.add_argument("--odds-api-market", type=str, required=False)
        parser.add_argument("--odds-api-match-id", type=str, required=False)
        parser.add_argument("--odds-api-team-name", type=str, required=False)

        parser.add_argument("--fpmm-address", type=str, required=False)

        parser.add_argument(
            "--metrics-server-port",
            type=int,
            default=9008,
            help="The port where the process must start the metrics server",
        )

        args = parser.parse_args(args)

        self.sync_interval = args.sync_interval

        self.min_tick = args.min_tick
        self.min_size = args.min_size

        # server to expose the metrics.
        self.metrics_server_port = args.metrics_server_port
        start_http_server(self.metrics_server_port)

        self.web3 = setup_web3(args)
        self.address = self.web3.eth.account.from_key(args.private_key).address

        self.bands_config = args.bands_config

        self.market = Market(
            args.condition_id,
            args.token_id_A,
            args.token_id_B,
        )

        self.clob_api = ClobApi(args)

        self.gas_station = GasStation(
            strat=GasStrategy(args.gas_strategy),
            w3=self.web3,
            url=args.gas_station_url,
            fixed=args.fixed_gas_price,
        )
        self.contracts = Contracts(self.web3, self.gas_station)

        self.price_feed_source = args.price_feed_source
        if self.price_feed_source == PriceFeedSource.CLOB:
            self.price_feed = PriceFeedClob(self.clob_api)
        # elif self.price_feed_source == PriceFeedSource.ODDS_API:
        #     odds_api = OddsAPI(
        #         api_key=args.odds_api_key,
        #         sport=args.odds_api_sport,
        #         region=args.odds_api_region,
        #         market=args.odds_api_market,
        #     )
        #     self.price_feed = PriceFeedOddsAPI(
        #         odds_api=odds_api,
        #         match_id=args.odds_api_match_id,
        #         team_name=args.odds_api_team_name,
        #     )

        self.order_book_manager = OrderBookManager(
            args.refresh_frequency, max_workers=1
        )
        self.order_book_manager.get_orders_with(
            lambda: self.clob_api.get_orders(self.market.condition_id)
        )
        self.order_book_manager.get_balances_with(lambda: self.get_balances())
        self.order_book_manager.cancel_orders_with(
            lambda order: self.clob_api.cancel_order(order.id)
        )
        self.order_book_manager.cancel_all_orders_with(
            lambda: self.clob_api.cancel_all_orders()
        )
        self.order_book_manager.start()

    def get_balances(self):
        """
        Fetch the onchain balances of collateral and conditional tokens for the keeper
        """
        self.logger.debug(f"Getting balances for address: {self.address}")

        collateral_balance = self.contracts.token_balance_of(
            self.clob_api.get_collateral_address(), self.address
        )
        token_A_balance = self.contracts.token_balance_of(
            self.clob_api.get_conditional_address(),
            self.address,
            self.market.token_id(Token.A),
        )
        token_B_balance = self.contracts.token_balance_of(
            self.clob_api.get_conditional_address(),
            self.address,
            self.market.token_id(Token.B),
        )
        gas_balance = self.contracts.gas_balance(self.address)

        keeper_balance_amount.labels(
            accountaddress=self.address,
            assetaddress=self.clob_api.get_collateral_address(),
            tokenid="-1",
        ).set(collateral_balance)
        keeper_balance_amount.labels(
            accountaddress=self.address,
            assetaddress=self.clob_api.get_conditional_address(),
            tokenid=self.market.token_id(Token.A),
        ).set(token_A_balance)
        keeper_balance_amount.labels(
            accountaddress=self.address,
            assetaddress=self.clob_api.get_conditional_address(),
            tokenid=self.market.token_id(Token.B),
        ).set(token_B_balance)
        keeper_balance_amount.labels(
            accountaddress=self.address,
            assetaddress="0x0",
            tokenid="-1",
        ).set(gas_balance)

        return {
            "collateral": collateral_balance,
            Token.A.value: token_A_balance,
            Token.B.value: token_B_balance,
        }

    def approve(self):
        """
        Approve the keeper on the collateral and conditional tokens
        """
        collateral = self.clob_api.get_collateral_address()
        conditional = self.clob_api.get_conditional_address()
        exchange = self.clob_api.get_exchange()

        self.contracts.max_approve_erc20(collateral, self.address, exchange)
        self.contracts.max_approve_erc1155(conditional, self.address, exchange)

    def main(self):
        with Lifecycle() as lifecycle:
            lifecycle.initial_delay(
                5
            )  # 5 second initial delay so that bg threads fetch the orderbook
            lifecycle.on_startup(self.startup)
            lifecycle.every(
                self.sync_interval, self.synchronize
            )  # Sync every 5s
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
        if (
            orderbook.balances.get("collateral") is None
            or orderbook.balances.get(Token.A.value) is None
            or orderbook.balances.get(Token.B.value) is None
        ):
            self.logger.debug("Balances invalid/non-existent")
            return

        for buy_token in Token:
            orders_by_type = [
                order
                for order in orderbook.orders
                if (self.buy_token(order) == buy_token)
            ]

            target_price = self.price_feed.get_price(
                self.market.token_id(buy_token)
            )

            self.logger.debug(
                f"Token {buy_token.name} target price: {target_price}"
            )

            self.synchronize_token(
                orderbook, bands, buy_token, orders_by_type, target_price
            )

        self.logger.debug("Synchronized orderbook!")

    def buy_token(self, order: Order):
        token = self.market.token(order.token_id)
        return token if order.side == Side.BUY else token.complement()

    def synchronize_token(
        self,
        orderbook: OrderBook,
        bands: Bands,
        buy_token: Token,
        orders: list[Order],
        target_price: float,
    ):
        sell_token = Token.complement(buy_token)
        cancellable_orders = bands.cancellable_orders(
            orders=orders,
            target_price=target_price,
        )

        if len(cancellable_orders) > 0:
            self.order_book_manager.cancel_orders(cancellable_orders)
            return

        # Do not place new orders if order book state is not confirmed
        if orderbook.orders_being_placed or orderbook.orders_being_cancelled:
            self.logger.debug(
                "Order book sync is in progress, not placing new orders"
            )
            return

        balance_locked_by_open_buys = sum(
            order.size * order.price
            for order in orders
            if order.side == Side.BUY
        )
        balance_locked_by_open_sells = sum(
            order.size for order in orders if order.side == Side.SELL
        )
        self.logger.debug(
            f"Collateral locked by buys: {balance_locked_by_open_buys}"
        )
        self.logger.debug(
            f"Token {sell_token.name} locked by sells: {balance_locked_by_open_sells}"
        )

        free_collateral_balance = (
            orderbook.balances.get("collateral") - balance_locked_by_open_buys
        )
        free_token_balance = (
            orderbook.balances.get(sell_token.value)
            - balance_locked_by_open_sells
        )

        self.logger.debug(
            f"Free collateral balance: {free_collateral_balance}"
        )
        self.logger.debug(f"Free token balance: {free_token_balance}")

        # Create new orders if needed
        new_orders = bands.new_orders(
            orders=orders,
            collateral_balance=free_collateral_balance,
            token_balance=free_token_balance,
            target_price=target_price,
        )

        if len(new_orders) > 0:
            self.logger.info(f"About to place {len(new_orders)} new orders!")
            self.place_orders(new_orders, buy_token, sell_token)

    def place_orders(
        self, new_orders: list[Order], buy_token: str, sell_token: str
    ):
        """
        Place new orders
        :param new_orders: list[Orders]
        """

        def place_order_function(new_order_to_be_placed: Order):
            size = new_order_to_be_placed.size
            side = new_order_to_be_placed.side
            price = new_order_to_be_placed.price

            token_id = (
                self.market.token_id(buy_token)
                if side == Side.BUY
                else self.market.token_id(sell_token)
            )

            order_id = self.clob_api.place_order(
                price=price, size=size, side=side, token_id=token_id
            )
            return Order(
                price=price,
                size=size,
                side=side,
                id=order_id,
                token_id=token_id,
            )

        for new_order in new_orders:
            self.order_book_manager.place_order(
                lambda new_order=new_order: place_order_function(new_order)
            )

    def shutdown(self):
        """
        Shut down the keeper
        """
        self.logger.info("Keeper shutting down...")
        self.order_book_manager.cancel_all_orders()
        self.logger.info("Keeper is shut down!")


if __name__ == "__main__":
    setup_logging()
    ClobMarketMakerKeeper(sys.argv[1:]).main()
