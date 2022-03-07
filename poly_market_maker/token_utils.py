import web3
import web3.constants

erc20_balance_of = """[{"constant": true,"inputs": [{"name": "_owner","type": "address"}],"name": "balanceOf","outputs": [{"name": "balance","type": "uint256"}],"payable": false,"stateMutability": "view","type": "function"}]"""
erc1155_balance_of = """[{"inputs": [{"internalType": "address","name": "account","type": "address"},{"internalType": "uint256","name": "id","type": "uint256"}],"name": "balanceOf","outputs": [{"internalType": "uint256","name": "","type": "uint256"}],"stateMutability": "view","type": "function"}]"""

erc20_approve = """[{"constant": false,"inputs": [{"name": "_spender","type": "address" },{ "name": "_value", "type": "uint256" }],"name": "approve","outputs": [{ "name": "", "type": "bool" }],"payable": false,"stateMutability": "nonpayable","type": "function"}]"""
erc1155_set_approval = """[{"inputs": [{ "internalType": "address", "name": "operator", "type": "address" },{ "internalType": "bool", "name": "approved", "type": "bool" }],"name": "setApprovalForAll","outputs": [],"stateMutability": "nonpayable","type": "function"}]"""

erc20_allowance = """[{"constant": true,"inputs": [{"name": "_owner","type": "address"},{"name": "_spender","type": "address"}],"name": "allowance","outputs": [{"name": "","type": "uint256"}],"payable": false,"stateMutability": "view","type": "function"}]"""
erc1155_is_approved_for_all = """[{"inputs": [{"internalType": "address","name": "account","type": "address"},{"internalType": "address","name": "operator","type": "address"}],"name": "isApprovedForAll","outputs": [{"internalType": "bool","name": "","type": "bool"}],"stateMutability": "view","type": "function"}]"""

DECIMALS = 10 ** 6

def balance_of_erc20(w3: web3.Web3, token: str, address: str):
    erc20 = w3.eth.contract(token, abi=erc20_balance_of)
    return erc20.functions.balanceOf(address).call()
    
def balance_of_erc1155(w3: web3.Web3, token:str, address: str, token_id: int):
    erc1155 = w3.eth.contract(token, abi=erc1155_balance_of)
    return erc1155.functions.balanceOf(address, token_id).call()

def is_approved_erc20(w3: web3.Web3, token:str, owner: str, spender: str):
    erc20 = w3.eth.contract(token, abi=erc20_allowance)
    allowance = erc20.functions.allowance(owner, spender).call()
    return allowance > 0

def is_approved_erc1155(w3: web3.Web3, token:str, owner: str, spender: str):
    erc1155 = w3.eth.contract(token, abi=erc1155_is_approved_for_all)
    approved = erc1155.functions.isApprovedForAll(owner, spender).call()
    return approved

def max_approve_erc20(w3: web3.Web3, token:str, owner: str, spender: str):
    if not is_approved_erc20(w3, token, owner, spender):
        erc20 = w3.eth.contract(token, abi=erc20_approve)
        txn_hash = erc20.functions.approve(spender, int(web3.constants.MAX_INT, base=16)).transact()
        return txn_hash

def max_approve_erc1155(w3: web3.Web3, token:str, owner: str, spender: str):
    if not is_approved_erc1155(w3, token, owner, spender):
        erc1155 = w3.eth.contract(token, abi=erc1155_set_approval)
        txn_hash = erc1155.functions.setApprovalForAll(spender, True).transact()
        return txn_hash

def token_balance_of(w3: web3.Web3, token:str, address: str, token_id =None):
    if token_id is None:
        bal = balance_of_erc20(w3, token, address)
    else:
        bal = balance_of_erc1155(w3, token, address, token_id)
    return float(bal / DECIMALS)
