from enum import Enum
from py_clob_client.order_builder.constants import BUY, SELL


class Side(Enum):
    BUY = BUY
    SELL = SELL

    @staticmethod
    def from_string(side: str):
        if side.lower() == Side.BUY.value.lower():
            return Side.BUY
        if side.lower() == Side.SELL.value.lower():
            return Side.SELL
        else:
            raise ValueError(
                f"side must be '{BUY}' or '{SELL}', got '{side}'."
            )


class Order:
    def __init__(
        self, size: float, price: float, side: Side, token_id: str, id=None
    ):
        self.size = size
        self.price = price
        self.side = side
        self.token_id = token_id
        self.id = id

    def __repr__(self):
        return f"Order[id={self.id}, price={self.price}, size={self.size}, side={self.side.value}, token_id={self.token_id}]"
