from enum import Enum

Collateral = "collateral"


class Token(Enum):
    A = "TokenA"
    B = "TokenB"

    def complement(self):
        return Token.B if self == Token.A else Token.A


class Market:
    def __init__(self, condition_id: str, token_id_a: str, token_id_b: str):
        assert isinstance(condition_id, str)
        assert isinstance(token_id_a, str)
        assert isinstance(token_id_b, str)

        self.condition_id = condition_id
        self.token_ids = {
            Token.A: token_id_a,
            Token.B: token_id_b
        }


    def token_id(self, token: Token) -> str:
        return self.token_ids[token]
    
    def token(self, token_id: str) -> Token:
        return Token.A if token_id == self.token_ids[Token.A] else Token.B

    def __repr__(self):
        return f"Market[condition_id={self.condition_id}, token_id_a={self.token_id_a}, token_id_b={self.token_id_b}]"
