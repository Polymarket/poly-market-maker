from enum import Enum


class Token(Enum):
    A = "tokenA"
    B = "tokenB"

    def complement(self):
        return Token.B if self == Token.A else Token.A


class Market:
    def __init__(self, condition_id: str, token_id_A: str, token_id_B: str):
        self.condition_id = condition_id
        self.token_id_A = token_id_A
        self.token_id_B = token_id_B

    def token_id(self, token: Token):
        return self.token_id_A if token == Token.A else self.token_id_B

    def token(self, token_id: str):
        return Token.A if int(token_id) == int(self.token_id_A) else Token.B

    def __repr__(self):
        return f"Market[condition_id={self.condition_id}, token_id_A={self.token_id_A}, token_id_B={self.token_id_B},]"
