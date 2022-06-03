import logging
import sys
import time

from .utils import randomize_default_price
from .order import Order
from .constants import OK
from .metrics import clob_requests_latency

from py_clob_client.client import ClobClient, ApiCreds, LimitOrderArgs, FilterParams

DEFAULT_PRICE = 0.5


class ClobApi:
    def __init__(self, token_id: str, args):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.token_id = token_id
        self.client: ClobClient = self._init_client(
            args.eth_key,
            args.chain_id,
            args.clob_api_url,
            args.clob_api_key,
            args.clob_api_secret,
            args.clob_api_passphrase,
        )

    def get_address(self):
        return self.client.get_address()

    def get_collateral_address(self):
        return self.client.get_collateral_address()

    def get_conditional_address(self):
        return self.client.get_conditional_address()

    def get_exchange(self):
        return self.client.get_exchange_address()

    def get_executor(self):
        return self.client.get_executor_address()

    def get_price(self):
        """
        Get the current price on the orderbook
        """
        self.logger.debug("Fetching midpoint price from the API...")
        start_time = time.time()
        try:
            resp = self.client.get_midpoint(self.token_id)
            clob_requests_latency.labels(method="get_midpoint", status="ok").observe(
                (time.time() - start_time)
            )
            if resp.get("mid") is not None:
                return float(resp.get("mid"))
        except Exception as e:
            self.logger.error(f"Error fetching current price from the CLOB API: {e}")
            clob_requests_latency.labels(method="get_midpoint", status="error").observe(
                (time.time() - start_time)
            )

        return self._rand_price()

    def _rand_price(self) -> float:
        price = randomize_default_price(DEFAULT_PRICE)
        self.logger.info(
            f"Could not fetch price from CLOB API, returning random price: {price}"
        )
        return price

    def get_orders(self):
        """
        Get open keeper orders on the orderbook
        """
        self.logger.debug("Fetching open keeper orders from the API...")
        start_time = time.time()
        try:
            resp = self.client.get_open_orders(FilterParams(market=self.token_id))
            clob_requests_latency.labels(method="get_open_orders", status="ok").observe(
                (time.time() - start_time)
            )
            if resp.get("orders") is not None:
                return [self._get_order(o) for o in resp.get("orders")]
        except Exception as e:
            self.logger.error(
                f"Error fetching keeper open orders from the CLOB API: {e}"
            )
            clob_requests_latency.labels(
                method="get_open_orders", status="error"
            ).observe((time.time() - start_time))
        return []

    def place_order(self, price, size, side):
        """
        Places a new order
        """
        self.logger.info(
            f"Placing a new order: Order[price={price},size={size},side={side}]"
        )
        start_time = time.time()
        try:
            resp = self.client.create_and_post_limit_order(
                LimitOrderArgs(
                    price=price, size=size, side=side, token_id=self.token_id
                )
            )
            clob_requests_latency.labels(
                method="create_and_post_limit_order", status="ok"
            ).observe((time.time() - start_time))
            order_id = None
            if resp and resp.get("success") and resp.get("orderID"):
                order_id = resp.get("orderID")
                self.logger.info(
                    f"Succesfully placed new order: Order[id={order_id},price={price},size={size},side={side}]!"
                )
                return order_id

            err_msg = resp.get("errorMsg")
            self.logger.error(
                f"Could not place new order! CLOB returned error: {err_msg}"
            )
        except Exception as e:
            self.logger.error(f"Request exception: failed placing new order: {e}")
            clob_requests_latency.labels(
                method="create_and_post_limit_order", status="error"
            ).observe((time.time() - start_time))
        return None

    def cancel_order(self, order_id):
        self.logger.info(f"Cancelling order {order_id}...")
        if order_id is None:
            self.logger.debug("Invalid order_id")
            return True

        start_time = time.time()
        try:
            resp = self.client.cancel(order_id)
            clob_requests_latency.labels(method="cancel", status="ok").observe(
                (time.time() - start_time)
            )
            return resp == OK
        except Exception as e:
            self.logger.error(f"Error cancelling order: {order_id}: {e}")
            clob_requests_latency.labels(method="cancel", status="error").observe(
                (time.time() - start_time)
            )
        return False

    def cancel_all_orders(self):
        self.logger.info("Cancelling all open keeper orders..")
        start_time = time.time()
        try:
            resp = self.client.cancel_all()
            clob_requests_latency.labels(method="cancel_all", status="ok").observe(
                (time.time() - start_time)
            )
            return resp == OK
        except Exception as e:
            self.logger.error(f"Error cancelling all orders: {e}")
            clob_requests_latency.labels(method="cancel_all", status="error").observe(
                (time.time() - start_time)
            )
        return False

    def _init_client(
        self,
        private_key,
        chain_id,
        clob_url,
        clob_api_key,
        clob_api_secret,
        clob_api_passphrase,
    ):
        creds = ApiCreds(clob_api_key, clob_api_secret, clob_api_passphrase)
        clob_client = ClobClient(clob_url, chain_id, private_key, creds)
        try:
            if clob_client.get_ok() == OK:
                self.logger.info("Connected to CLOB API!")
                self.logger.info(
                    "CLOB Keeper address: {}".format(clob_client.get_address())
                )
                return clob_client
        except:
            self.logger.error("Unable to connect to CLOB API, shutting down!")
            sys.exit(1)

    def _get_order(self, order_dict: dict):
        size = order_dict.get("size")
        side = order_dict.get("side")
        price = order_dict.get("price")
        order_id = order_dict.get("orderID")
        return Order(size=float(size), price=float(price), side=side, id=order_id)
