from .constants import BUY, SELL, A, B


class Market:
    def __init__(self, condition_id: str, token_id_A: float, token_id_B: str):
        self.condition_id = condition_id
        self.token_id_A = token_id_A
        self.token_id_B = token_id_B

    def token_id(self, type: str, side=BUY):
        if side is BUY:
            return self.token_id_A if type is A else self.token_id_B
        else:
            return self.token_id_B if type is A else self.token_id_A

    def __repr__(self):
        return f"Market[condition_id={self.condition_id}, token_id_A={self.token_id_A}, token_id_B={self.token_id_B},]"
