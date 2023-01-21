import logging
from web3 import Web3

from .contracts import Contracts
from .gas import GasStation, GasStrategy


class FPMM:
    """Fixed product market maker price utils"""

    def __init__(self, contracts: Contracts):
        self.logger = logging.getLogger(self.__class__.__name__)

        if not contracts:
            self.logger.fatal(
                "contracts parameter is mandatory and can not be empty"
            )
            raise Exception(
                "contracts parameter is mandatory and can not be empty"
            )

        self.contracts = contracts

    def get_price(
        self,
        conditional_token: str,
        fpmm: str,
        token_id: str,
        token_complement_id: str,
    ) -> float:

        token_balance = self.contracts.balance_of_erc1155(
            conditional_token, fpmm, token_id
        )

        complement_balance = self.contracts.balance_of_erc1155(
            conditional_token, fpmm, token_complement_id
        )

        price = 1 - (token_balance / (token_balance + complement_balance))

        return price
