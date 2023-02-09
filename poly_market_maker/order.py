from enum import Enum
from py_clob_client.order_builder.constants import BUY, SELL


class Side(Enum):
    BUY = BUY
    SELL = SELL

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            for side in Side:
                if value.lower() == side.value.lower():
                    return side
        return super()._missing_(value)


class Order:
    def __init__(
        self, size: float, price: float, side: Side, token_id: str, id=None
    ):
        assert isinstance(token_id, str)

        self.size = size
        self.price = price
        self.side = side
        self.token_id = token_id
        self.id = id

    def __repr__(self):
        return f"Order[id={self.id}, price={self.price}, size={self.size}, side={self.side.value}, token_id={self.token_id}]"
