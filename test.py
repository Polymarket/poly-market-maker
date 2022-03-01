import web3

from poly_market_maker.token_utils import balance_of_erc20, token_balance_of


def main():

    # w3 = web3.Web3()
    keeper = "0xe3d9BFA896aF6988f80027bfd13440A42C5ed02b"
    # token_address = "0x2E8DCfE708D44ae2e406a1c02DFE2Fa13012f961"
    token_address = "0x7D8610E9567d2a6C9FBf66a5A13E9Ba8bb120d43"
    token_id=16678291189211314787145083999015737376658799626183230671758641503291735614088
    # print(f"Balance of: {token_balance_of(w3, token_address, keeper)}")
    print(f"Balance of: {token_balance_of(w3, token_address, keeper, token_id)}")
    pass


main()