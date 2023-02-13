
from poly_market_maker.ct_helpers import CTHelpers
from poly_market_maker.token import Token

class Market:
    def __init__(self, condition_id: str, collateral_address: str):
        assert isinstance(condition_id, str)

        self.condition_id = condition_id
        self.token_ids = {
            Token.A: CTHelpers.get_token_id(condition_id, collateral_address, 0),
            Token.B: CTHelpers.get_token_id(condition_id, collateral_address, 1)
        }


    def token_id(self, token: Token) -> str:
        return self.token_ids[token]
    
    def token(self, token_id: str) -> Token:
        return Token.A if token_id == self.token_ids[Token.A] else Token.B

    def __repr__(self):
        return f"Market[condition_id={self.condition_id}, token_id_a={self.token_ids[Token.A]}, token_id_b={self.token_ids[Token.B]}]"


