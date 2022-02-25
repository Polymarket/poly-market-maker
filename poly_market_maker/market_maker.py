import argparse
import logging
import sys

from py_clob_client.client import ClobClient, ApiCreds



class ClobMarketMakerKeeper:
    """Market maker keeper on Polymarket CLOB"""

    logger = logging.getLogger()
    logging.basicConfig(format='%(asctime)-15s %(levelname)-8s %(message)s',
                        level=(logging.DEBUG))

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

        # TODO: for now will only allow MMing on a single market/tokenID
        parser.add_argument("--token-id", type=str, required=True, help="The tokenID of the market being made")

        # parser.add_argument("--config", type=str, required=True, help="Bands configuration file")

        # parser.add_argument("--refresh-frequency", type=int, default=3,
        #                     help="Order book refresh frequency (in seconds, default: 3)")
        # TODO: remove unused args
        # parser.add_argument("--pair", type=str, required=True,
        #                     help="Token pair (sell/buy) on which the keeper will operate")

        # parser.add_argument("--buy-token-address", type=str, required=True,
        #                     help="Ethereum address of the buy token")

        # parser.add_argument("--sell-token-address", type=str, required=True,
        #                     help="Ethereum address of the sell token")

        # parser.add_argument("--price-feed", type=str, required=True,
        #                     help="Source of price feed")

        # parser.add_argument("--price-feed-expiry", type=int, default=120,
        #                     help="Maximum age of the price feed (in seconds, default: 120)")

        # parser.add_argument("--spread-feed", type=str,
        #                     help="Source of spread feed")

        # parser.add_argument("--spread-feed-expiry", type=int, default=3600,
        #                     help="Maximum age of the spread feed (in seconds, default: 3600)")

        # parser.add_argument("--control-feed", type=str,
        #                     help="Source of control feed")

        # parser.add_argument("--control-feed-expiry", type=int, default=86400,
        #                     help="Maximum age of the control feed (in seconds, default: 86400)")

        # parser.add_argument("--order-history", type=str,
        #                     help="Endpoint to report active orders to")

        # parser.add_argument("--order-history-every", type=int, default=30,
        #                     help="Frequency of reporting active orders (in seconds, default: 30)")

        # parser.add_argument("--order-expiry", type=int, required=True,
        #                     help="Expiration time of created orders (in seconds)")

        self.args = parser.parse_args(args)
        self.client = self._init_client(self.args)

        # the order manager will be the main entry point 


    def _init_client(self, args):
        creds = ApiCreds(args.clob_api_key, args.clob_api_secret, args.clob_api_passphrase)
        clob_client = ClobClient(args.clob_api_url, args.chain_id, args.eth_key, creds)
        try:
            ok = clob_client.get_ok()
            if ok == "OK":
                self.logger.info("Connected to CLOB API!")
                self.logger.info("CLOB Keeper address: {}".format(clob_client.get_address()))
                return clob_client
        except:
            self.logger.error("Unable to connect to CLOB API, shutting down...")
            return None


    def main(self):
        # with Lifecycle(self.web3) as lifecycle:
        #     lifecycle.initial_delay(10)
        #     lifecycle.on_startup(self.startup)
        #     lifecycle.every(1, self.synchronize_orders)
        #     lifecycle.on_shutdown(self.shutdown)
        pass

    def shutdown(self):
        # self.order_book_manager.cancel_all_orders()
        pass    


if __name__ == '__main__':
    ClobMarketMakerKeeper(sys.argv[1:]).main()
