import logging
import sys

from .order import Order
from py_clob_client.client import ClobClient, ApiCreds, LimitOrderArgs


class ClobApi:

    logger = logging.getLogger(__name__)

    def __init__(self, tokenId: str, args):
        self.tokenId = tokenId
        self.client: ClobClient = self._init_client(
            args.eth_key, 
            args.chain_id, 
            args.clob_api_url, 
            args.clob_api_key, 
            args.clob_api_secret, 
            args.clob_api_passphrase
        )

    def get_address(self):
        # TODO: on client make sure to return checksummed address
        return self.client.get_address()

    def get_collateral_address(self):
        return self.client.get_collateral_address()

    def get_conditional_address(self):
        return self.client.get_conditional_address()

    def get_price(self):
        """
        Get the current price on the orderbook
        """
        try:
            resp = self.client.get_midpoint(self.tokenId)
            if resp.get("mid") is not None:
                return float(resp.get("mid"))
        except Exception as e:
            print(f"Error fetching current price from the CLOB API: {e}")
            self.logger.error(f"Error fetching current price from the CLOB API: {e}")
        
        return None

    def get_orders(self):
        """
        """
        try:
            resp = self.client.get_open_orders(self.tokenId)
            if resp.get("orders") is not None:
                return [self._get_order(o) for o in resp.get("orders")]
        except Exception as e:
            #TODO: replace with logger
            print(f"Error fetching keeper open orders from the CLOB API: {e}")
            self.logger.error(f"Error fetching keeper open orders from the CLOB API: {e}")
        return None

    def place_order(self, price, size, side):
        """
        Places a new order
        """
        try:
            resp = self.client.create_and_post_limit_order(
                LimitOrderArgs(price=price, size=size, side=side, token_id=self.tokenId)
            )
            if resp and resp.get("Success"):
                return resp.get("orderID")
        except Exception as e:
            print(f"Error placing new order on the CLOB API: {e}")
            self.logger.error(f"Error placing new order on the CLOB API: {e}")
        return None

    def cancel_order(self, order_id):
        try:
            resp = self.client.cancel(order_id)
            return self._validate_cancel_response(resp)
        except Exception as e:
            #TODO: replace with logger
            self.logger.error(f"Error cancelling order: {order_id}: {e}")
            print(f"Error cancelling order: {order_id}: {e}")
        return None

    def cancel_all_orders(self):
        try:
            resp = self.client.cancel_all()
            return self._validate_cancel_response(resp)
        except Exception as e:
            self.logger.error(f"Error cancelling all orders: {e}")
            print(f"Error cancelling all orders: {e}")
        return None

    def _init_client(self, private_key, chain_id, clob_url, clob_api_key, clob_api_secret, clob_api_passphrase):
        creds = ApiCreds(clob_api_key, clob_api_secret, clob_api_passphrase)
        clob_client = ClobClient(clob_url, chain_id, private_key, creds)
        try:
            ok = clob_client.get_ok()
            if ok == "OK":
                self.logger.info("Connected to CLOB API!")
                self.logger.info("CLOB Keeper address: {}".format(clob_client.get_address()))
                return clob_client
        except:
            self.logger.error("Unable to connect to CLOB API, shutting down...")
            sys.exit(1)

    def _get_order(self, order_dict: dict):
        size = order_dict.get("size")
        side = order_dict.get("side")
        price = order_dict.get("price")
        order_id = order_dict.get("orderID")
        #TODO: validation on received size/price?
        return Order(size=float(size), price=float(price), side=side, order_id=order_id)
        

    def _validate_cancel_response(self, resp):
        return resp == "OK"


