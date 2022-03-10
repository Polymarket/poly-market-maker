import logging
import web3
import web3.constants

from .gas import GasStation


erc20_balance_of = """[{"constant": true,"inputs": [{"name": "_owner","type": "address"}],"name": "balanceOf","outputs": [{"name": "balance","type": "uint256"}],"payable": false,"stateMutability": "view","type": "function"}]"""
erc1155_balance_of = """[{"inputs": [{"internalType": "address","name": "account","type": "address"},{"internalType": "uint256","name": "id","type": "uint256"}],"name": "balanceOf","outputs": [{"internalType": "uint256","name": "","type": "uint256"}],"stateMutability": "view","type": "function"}]"""

erc20_approve = """[{"constant": false,"inputs": [{"name": "_spender","type": "address" },{ "name": "_value", "type": "uint256" }],"name": "approve","outputs": [{ "name": "", "type": "bool" }],"payable": false,"stateMutability": "nonpayable","type": "function"}]"""
erc1155_set_approval = """[{"inputs": [{ "internalType": "address", "name": "operator", "type": "address" },{ "internalType": "bool", "name": "approved", "type": "bool" }],"name": "setApprovalForAll","outputs": [],"stateMutability": "nonpayable","type": "function"}]"""

erc20_allowance = """[{"constant": true,"inputs": [{"name": "_owner","type": "address"},{"name": "_spender","type": "address"}],"name": "allowance","outputs": [{"name": "","type": "uint256"}],"payable": false,"stateMutability": "view","type": "function"}]"""
erc1155_is_approved_for_all = """[{"inputs": [{"internalType": "address","name": "account","type": "address"},{"internalType": "address","name": "operator","type": "address"}],"name": "isApprovedForAll","outputs": [{"internalType": "bool","name": "","type": "bool"}],"stateMutability": "view","type": "function"}]"""

DECIMALS = 10 ** 6


class Contracts:
    def __init__(self, w3: web3.Web3, gas_station: GasStation):
        self.w3 = w3
        self.gas_station = gas_station
        self.logger = logging.getLogger(self.__class__.__name__)

    def balance_of_erc20(self, token: str, address: str):
        erc20 = self.w3.eth.contract(token, abi=erc20_balance_of)
        return erc20.functions.balanceOf(address).call()
        
    def balance_of_erc1155(self, token:str, address: str, token_id: int):
        erc1155 = self.w3.eth.contract(token, abi=erc1155_balance_of)
        return erc1155.functions.balanceOf(address, token_id).call()

    def is_approved_erc20(self, token:str, owner: str, spender: str):
        erc20 = self.w3.eth.contract(token, abi=erc20_allowance)
        allowance = erc20.functions.allowance(owner, spender).call()
        return allowance > 0
        
    def is_approved_erc1155(self, token:str, owner: str, spender: str):
        erc1155 = self.w3.eth.contract(token, abi=erc1155_is_approved_for_all)
        approved = erc1155.functions.isApprovedForAll(owner, spender).call()
        return approved
        
    def max_approve_erc20(self, token:str, owner: str, spender: str):
        if not self.is_approved_erc20(token, owner, spender):
            erc20 = self.w3.eth.contract(token, abi=erc20_approve)
            self.logger.info(f"Max approving ERC20 token {token} on spender {spender}...")
            txn_hash_bytes = erc20.functions.approve(spender, int(web3.constants.MAX_INT, base=16)).transact({"gasPrice": self.gas_station.get_gas_price()})
            txn_hash_hex = self.w3.toHex(txn_hash_bytes)
            self.logger.info(f"ERC20 approve transaction hash: {txn_hash_hex}")
            return txn_hash_hex

    def max_approve_erc1155(self, token:str, owner: str, spender: str):
        if not self.is_approved_erc1155(token, owner, spender):
            self.logger.info(f"Max approving ERC1155 token {token} on spender {spender}...")
            erc1155 = self.w3.eth.contract(token, abi=erc1155_set_approval)
            txn_hash_bytes = erc1155.functions.setApprovalForAll(spender, True).transact({"gasPrice": self.gas_station.get_gas_price()})
            txn_hash_hex = self.w3.toHex(txn_hash_bytes)
            self.logger.info(f"ERC1155 approve transaction hash: {txn_hash_hex}")
            return txn_hash_hex

    def token_balance_of(self, token:str, address: str, token_id =None):
        if token_id is None:
            bal = self.balance_of_erc20(token, address)
        else:
            bal = self.balance_of_erc1155(token, address, token_id)
        return float(bal / DECIMALS)




