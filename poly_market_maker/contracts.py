import logging
import web3
import web3.constants
import json
from .gas import GasStation
from .metrics import chain_requests_counter


erc20_abi = json.loads(
    '[{"constant": true,"inputs": [{"name": "_owner","type": "address"}],"name": "balanceOf","outputs": [{"name": "balance","type": "uint256"}],"payable": false,"stateMutability": "view","type": "function"}],[{"constant": false,"inputs": [{"name": "_spender","type": "address" },{ "name": "_value", "type": "uint256" }],"name": "approve","outputs": [{ "name": "", "type": "bool" }],"payable": false,"stateMutability": "nonpayable","type": "function"}],[{"constant": true,"inputs": [{"name": "_owner","type": "address"},{"name": "_spender","type": "address"}],"name": "allowance","outputs": [{"name": "","type": "uint256"}],"payable": false,"stateMutability": "view","type": "function"}]'
)

# TO-DO: FIX
DECIMALS = 10**6


class Contracts:
    def __init__(self, w3: web3.Web3, gas_station: GasStation):
        self.w3 = w3
        self.gas_station = gas_station
        self.logger = logging.getLogger(self.__class__.__name__)

    def balance_of_erc20(self, token: str, address: str):
        erc20 = self.w3.eth.contract(token, abi=erc20_abi)
        bal = None

        try:
            bal = erc20.functions.balanceOf(address).call()
            chain_requests_counter.labels(
                method="ERC20 balanceOf", status="ok"
            ).inc()
        except Exception as e:
            self.logger.error(f"Error ERC20 balanceOf: {e}")
            chain_requests_counter.labels(
                method="ERC20 balanceOf", status="error"
            ).inc()
            raise e

        return bal

    def is_approved_erc20(self, token: str, owner: str, spender: str):
        erc20 = self.w3.eth.contract(token, abi=erc20_abi)

        try:
            allowance = erc20.functions.allowance(owner, spender).call()
            chain_requests_counter.labels(
                method="allowance", status="ok"
            ).inc()
        except Exception as e:
            self.logger.error(f"Error allowance: {e}")
            chain_requests_counter.labels(
                method="allowance", status="error"
            ).inc()
            raise e

        return allowance > 0

    def max_approve_erc20(self, token: str, owner: str, spender: str):
        if not self.is_approved_erc20(token, owner, spender):
            erc20 = self.w3.eth.contract(token, abi=erc20_abi)
            self.logger.info(
                f"Max approving ERC20 token {token} on spender {spender}..."
            )

            try:
                txn_hash_bytes = erc20.functions.approve(
                    spender, int(web3.constants.MAX_INT, base=16)
                ).transact({"gasPrice": self.gas_station.get_gas_price()})
                chain_requests_counter.labels(
                    method="approve", status="ok"
                ).inc()
            except Exception as e:
                self.logger.error(f"Error approve: {e}")
                chain_requests_counter.labels(
                    method="approve", status="error"
                ).inc()
                raise e

            txn_hash_hex = self.w3.toHex(txn_hash_bytes)
            self.logger.info(f"ERC20 approve transaction hash: {txn_hash_hex}")
            return txn_hash_hex

    def token_balance_of(self, token: str, address: str):
        bal = self.balance_of_erc20(token, address)

        return float(bal / DECIMALS)

    def gas_balance(self, address):
        bal = None

        try:
            bal = self.w3.eth.get_balance(address)
            chain_requests_counter.labels(
                method="get_balance", status="ok"
            ).inc()
        except Exception as e:
            self.logger.error(f"Error get_balance: {e}")
            chain_requests_counter.labels(
                method="get_balance", status="error"
            ).inc()
            raise e

        return self.w3.fromWei(bal, "ether")
