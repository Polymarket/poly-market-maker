import web3

erc20_balance_of = """[{"constant": true,"inputs": [{"name": "_owner","type": "address"}],"name": "balanceOf","outputs": [{"name": "balance","type": "uint256"}],"payable": false,"stateMutability": "view","type": "function"}]"""
erc1155_balance_of = """[{"inputs": [{"internalType": "address","name": "account","type": "address"},{"internalType": "uint256","name": "id","type": "uint256"}],"name": "balanceOf","outputs": [{"internalType": "uint256","name": "","type": "uint256"}],"stateMutability": "view","type": "function"}]"""

DECIMALS = 10 ** 6

def balance_of_erc20(w3: web3.Web3, token: str, address: str):
    erc20 = w3.eth.contract(token, abi=erc20_balance_of)
    return erc20.functions.balanceOf(address).call()
    
def balance_of_erc1155(w3: web3.Web3, token:str, address: str, token_id: int):
    erc1155 = w3.eth.contract(token, abi=erc1155_balance_of)
    return erc1155.functions.balanceOf(address, token_id).call()   

def token_balance_of(w3: web3.Web3, token:str, address: str, token_id =None):
    if token_id is None:
        bal = balance_of_erc20(w3, token, address)
    else:
        bal = balance_of_erc1155(w3, token, address, token_id)
    return float(bal / DECIMALS)
