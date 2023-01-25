class Order:
    def __init__(
        self, size: float, price: float, side: str, token_id=0, id=None
    ):
        self.size = size
        self.price = price
        self.side = side
        self.token_id = token_id
        self.id = id

    def __repr__(self):
        return f"Order[id={self.id}, price={self.price}, size={self.size}, side={self.side}, token_id={self.token_id}]"
