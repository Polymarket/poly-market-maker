import itertools
import logging

from .utils import math_round_down, math_round_up

from .constants import BUY, SELL, MIN_TICK
from .order import Order


class Band:
    def __init__(
        self,
        min_margin: float,
        avg_margin: float,
        max_margin: float,
        min_amount: float,
        avg_amount: float,
        max_amount: float,
    ):
        self.logger = logging.getLogger(self.__class__.__name__)
        assert isinstance(min_margin, float)
        assert isinstance(avg_margin, float)
        assert isinstance(max_margin, float)
        assert isinstance(min_amount, float)
        assert isinstance(avg_amount, float)
        assert isinstance(max_amount, float)

        self.min_margin = min_margin
        self.avg_margin = avg_margin
        self.max_margin = max_margin
        self.min_amount = min_amount
        self.avg_amount = avg_amount
        self.max_amount = max_amount

        assert self.min_amount >= float(0)
        assert self.avg_amount >= float(0)
        assert self.max_amount >= float(0)
        assert self.min_amount <= self.avg_amount
        assert self.avg_amount <= self.max_amount

        assert self.min_margin <= self.avg_margin
        assert self.avg_margin <= self.max_margin
        assert self.min_margin < self.max_margin

    def order_price(self, order) -> float:
        raise NotImplemented()

    def type(self) -> str:
        raise NotImplemented()

    def excessive_orders(
        self, orders: list, target_price: float, is_first_band: bool, is_last_band: bool
    ):
        """Return orders which need to be cancelled to bring the total order amount in the band below maximum."""
        self.logger.debug(f"Running excessive orders for {self.type()}")
        # Get all orders which are currently present in the band.
        orders_in_band = [
            order for order in orders if self.includes(order, target_price)
        ]
        orders_total = sum(order.size for order in orders_in_band)

        # The sorting in which we remove orders depends on which band we are in.
        # * In the first band we start cancelling with orders closest to the target price.
        # * In the last band we start cancelling with orders furthest from the target price.
        # * In remaining cases we remove orders starting from the smallest one.
        if is_first_band:
            sorting = lambda order: abs(order.price - target_price)
            reverse = True

        elif is_last_band:
            sorting = lambda order: abs(order.price - target_price)
            reverse = False

        else:
            sorting = lambda order: order.size
            reverse = True

        orders_to_leave = sorted(orders_in_band, key=sorting, reverse=reverse)

        # Keep removing orders until their total amount stops being greater than `maxAmount`.
        while sum(order.size for order in orders_to_leave) > self.max_amount:
            orders_to_leave.pop()

        result = set(orders_in_band) - set(orders_to_leave)
        if len(result) > 0:
            self.logger.info(
                f"{self.type().capitalize()} band (spread <{self.min_margin}, {self.max_margin}>,"
                f" amount <{self.min_amount}, {self.max_amount}>) has amount {orders_total}, scheduling"
                f" {len(result)} order(s) for cancellation: {', '.join(map(lambda o: '#' + str(o.id), result))}"
            )

        return result

    def __repr__(self):
        return f"Band[type={self.type()}, spread<{self.min_margin}, {self.max_margin}>, amount<{self.min_amount}, {self.max_amount}>]"

    def __str__(self):
        return self.__repr__()


class BuyBand(Band):
    def __init__(self, dictionary: dict):
        super().__init__(
            min_margin=float(dictionary["minMargin"]),
            avg_margin=float(dictionary["avgMargin"]),
            max_margin=float(dictionary["maxMargin"]),
            min_amount=float(dictionary["minAmount"]),
            avg_amount=float(dictionary["avgAmount"]),
            max_amount=float(dictionary["maxAmount"]),
        )

    def order_price(self, order) -> float:
        return order.price

    def includes(self, order, target_price: float) -> bool:
        # For Buys, the min_margin will produce the price_max
        # E.g target=0.5, min_margin=0.01 = 0.5 * (1- 0.01) = 0.495
        #     target=0.5, max_margin=0.20 = 0.5 * (1- 0.2) = 0.4
        # self.logger.info(f"Included in band check...")
        # self.logger.info(f"target_price: {target_price}")
        # self.logger.info(f"min_margin: {self.min_margin}")
        # self.logger.info(f"max_margin: {self.max_margin}")
        price_max = self._apply_margin(target_price, self.min_margin)
        price_min = self._apply_margin(target_price, self.max_margin)
        # self.logger.info(f"price_min: {price_min}")
        # self.logger.info(f"price_max: {price_max}")
        included = (order.price <= price_max) and (order.price > price_min)
        # self.logger.info(f"{order} is included in band: {self}?: {included}")
        return included

    def type(self) -> str:
        return "buy"

    def avg_price(self, target_price: float) -> float:
        return self._apply_margin(target_price, self.avg_margin)

    @staticmethod
    def _apply_margin(price: float, margin: float) -> float:
        return price * (1 - margin)


class SellBand(Band):
    def __init__(self, dictionary: dict):
        super().__init__(
            min_margin=float(dictionary["minMargin"]),
            avg_margin=float(dictionary["avgMargin"]),
            max_margin=float(dictionary["maxMargin"]),
            min_amount=float(dictionary["minAmount"]),
            avg_amount=float(dictionary["avgAmount"]),
            max_amount=float(dictionary["maxAmount"]),
        )

    def type(self) -> str:
        return "sell"

    def includes(self, order, target_price: float) -> bool:
        price_min = self._apply_margin(target_price, self.min_margin)
        price_max = self._apply_margin(target_price, self.max_margin)
        included = (order.price < price_max) and (order.price >= price_min)
        self.logger.debug(f"{order} is included in band: {self}?: {included}")
        return included

    def avg_price(self, target_price: float) -> float:
        return self._apply_margin(target_price, self.avg_margin)

    @staticmethod
    def _apply_margin(price: float, margin: float) -> float:
        return price * (1 + margin)


class Bands:
    @staticmethod
    def read(config: dict):
        assert isinstance(config, dict)

        try:
            buy_bands = list(map(BuyBand, config["buyBands"]))
            sell_bands = list(map(SellBand, config["sellBands"]))

        except Exception as e:
            logging.getLogger().exception(
                f"Config file is invalid ({e}). Treating the config file as it has no bands."
            )

            buy_bands = []
            sell_bands = []

        return Bands(buy_bands=buy_bands, sell_bands=sell_bands)

    def __init__(self, buy_bands: list, sell_bands: list):
        self.logger = logging.getLogger(self.__class__.__name__)
        assert isinstance(buy_bands, list)
        assert isinstance(sell_bands, list)

        self.buy_bands = buy_bands
        self.sell_bands = sell_bands

        if self._bands_overlap(self.buy_bands) or self._bands_overlap(self.sell_bands):
            self.logger.error("Bands in the config file overlap!")
            raise Exception("Bands in the config file overlap!")
    
    @staticmethod
    def _derive_buy_band(price: float, min_price: float, avg_price: float, max_price: float, min_amount:float, avg_amount:float, max_amount:float) -> BuyBand:
        # looks like I have this switched. THis should be for sell

        return BuyBand(
            {
                "minMargin": round(((price - max_price) / price), 4),
                "avgMargin": round(((price - avg_price) / price), 4),
                "maxMargin": round(((price - min_price) / price), 4),
                "minAmount": min_amount,
                "avgAmount": avg_amount,
                "maxAmount": max_amount,
            }
        )

    @staticmethod
    def _derive_sell_band(price: float, min_price: float, avg_price: float, max_price: float, min_amount:float, avg_amount:float, max_amount:float) -> SellBand:

        return SellBand(
            {
                "minMargin":  round(((min_price - price) / price), 4),
                "avgMargin":  round(((avg_price - price) / price), 4),
                "maxMargin":  round(((max_price - price) / price), 4),
                "minAmount": min_amount,
                "avgAmount": avg_amount,
                "maxAmount": max_amount,
            }
        )

    def _calculate_virtual_buy_bands(self, price: float) -> list:
        # looks like I have this switched. THis should be for sell
        if price <= 0.0:
            return []
        min_price = 1.0
        avg_price = 1.0
        max_price = 1.0
        virtual_buy_bands = []
        for band in self.buy_bands:
            band_min_price = math_round_down(band._apply_margin(price, band.max_margin), 2)
            band_avg_price = math_round_down(band._apply_margin(price, band.avg_margin), 2)
            band_max_price = math_round_down(band._apply_margin(price, band.min_margin), 2)
            if band_min_price <= 0.0 or band_avg_price <= 0.0 or band_max_price <= 0.0:
                continue
            while band_min_price > min_price:
                band_min_price -= MIN_TICK
                band_avg_price -= MIN_TICK
                band_max_price -= MIN_TICK
            if band_avg_price == band_min_price:
                band_min_price -= MIN_TICK
            min_price = band_min_price
            avg_price = band_avg_price
            max_price = band_max_price
            virtual_buy_bands.append(self._derive_buy_band(price, band_min_price, band_avg_price, band_max_price, band.min_amount, band.avg_amount, band.max_amount))
        return virtual_buy_bands


    def _calculate_virtual_sell_bands(self, price: float) -> list:
        if price <= 0.0:
            return []
        min_price = 0
        avg_price = 0
        max_price = 0
        virtual_sell_bands = []
        for band in self.sell_bands:
            band_min_price = math_round_up(band._apply_margin(price, band.min_margin), 2)
            band_avg_price = math_round_up(band._apply_margin(price, band.avg_margin), 2)
            band_max_price = math_round_up(band._apply_margin(price, band.max_margin), 2)
            while band_min_price < max_price:
                band_min_price += MIN_TICK
                band_avg_price += MIN_TICK
                band_max_price += MIN_TICK
            if band_avg_price == band_max_price:
                band_max_price += MIN_TICK
            min_price = band_min_price
            avg_price = band_avg_price
            max_price = band_max_price
            virtual_sell_bands.append(self._derive_sell_band(price, band_min_price, band_avg_price, band_max_price, band.min_amount, band.avg_amount, band.max_amount))
        return virtual_sell_bands

    def _excessive_sell_orders(self, our_sell_orders: list, target_price: float):
        """Return sell orders which need to be cancelled to bring total amounts within all sell bands below maximums."""
        assert isinstance(our_sell_orders, list)
        assert isinstance(target_price, float)

        bands = self.sell_bands
        for band in bands:
            for order in band.excessive_orders(
                our_sell_orders, target_price, band == bands[0], band == bands[-1]
            ):
                yield order

    def _excessive_buy_orders(self, our_buy_orders: list, target_price: float):
        """Return buy orders which need to be cancelled to bring total amounts within all buy bands below maximums."""
        assert isinstance(our_buy_orders, list)
        assert isinstance(target_price, float)

        bands = self.buy_bands

        for band in bands:
            for order in band.excessive_orders(
                our_buy_orders, target_price, band == bands[0], band == bands[-1]
            ):
                yield order

    def _outside_any_band_orders(self, orders: list, bands: list, target_price: float):
        """Return buy or sell orders which need to be cancelled as they do not fall into any buy or sell band."""
        assert isinstance(orders, list)
        assert isinstance(bands, list)
        assert isinstance(target_price, float)

        for order in orders:
            if not any(band.includes(order, target_price) for band in bands):
                self.logger.info(
                    f"Order #{order.id} doesn't belong to any band, scheduling it for cancellation"
                )

                yield order

    def cancellable_orders( #here
        self, our_buy_orders: list, our_sell_orders: list, target_price: float
    ) -> list:
        assert isinstance(our_buy_orders, list)
        assert isinstance(our_sell_orders, list)
        assert isinstance(target_price, float)

        if target_price is None:
            self.logger.debug("Cancelling all buy orders as no buy price is available.")
            buy_orders_to_cancel = our_buy_orders

        else:
            buy_orders_to_cancel = list(
                itertools.chain(
                    self._excessive_buy_orders(our_buy_orders, target_price),
                    self._outside_any_band_orders(
                        our_buy_orders, self._calculate_virtual_buy_bands(target_price), target_price
                    ),
                )
            )

        if target_price is None:
            self.logger.debug(
                "Cancelling all sell orders as no sell price is available."
            )
            sell_orders_to_cancel = our_sell_orders

        else:
            sell_orders_to_cancel = list(
                itertools.chain(
                    self._excessive_sell_orders(our_sell_orders, target_price),
                    self._outside_any_band_orders(
                        our_sell_orders, self._calculate_virtual_sell_bands(target_price), target_price #here
                    ),
                )
            )

        return buy_orders_to_cancel + sell_orders_to_cancel

    def new_orders( #here
        self,
        our_buy_orders: list,
        our_sell_orders: list,
        our_buy_balance: float,
        our_sell_balance: float,
        target_price: float,
    ) -> list:
        assert isinstance(our_buy_orders, list)
        assert isinstance(our_sell_orders, list)
        assert isinstance(our_buy_balance, float)
        assert isinstance(our_sell_balance, float)
        assert isinstance(target_price, float)

        if target_price is not None:
            new_buy_orders = (
                self._new_buy_orders(our_buy_orders, our_buy_balance, target_price)
                if target_price is not None
                else ([], float(0))
            )

            new_sell_orders = (
                self._new_sell_orders(our_sell_orders, our_sell_balance, target_price)
                if target_price is not None
                else ([], float(0))
            )

            return new_buy_orders + new_sell_orders

        else:
            return []

    def _new_sell_orders(
        self, our_sell_orders: list, our_sell_balance: float, target_price: float
    ):
        """
        Return sell orders which need to be placed to bring total amounts within all sell bands above minimums
        """
        assert isinstance(our_sell_orders, list)
        assert isinstance(our_sell_balance, float)
        assert isinstance(target_price, float)

        new_orders = []

        for band in self._calculate_virtual_sell_bands(target_price): #here
            orders = [
                order for order in our_sell_orders if band.includes(order, target_price)
            ]
            total_amount = sum(order.size for order in orders)
            if total_amount < band.min_amount:
                price = math_round_up(band.avg_price(target_price), 2)
                size = math_round_down(
                    min(band.avg_amount - total_amount, our_sell_balance), 2
                )
                if (price > float(0)) and (size > float(0)):
                    self.logger.debug(
                        f"{band} has existing amount {total_amount},"
                        f" creating new sell order with price {price} and size: {size}"
                    )

                    our_sell_balance = our_sell_balance - size
                    new_orders.append(Order(price=price, size=size, side=SELL))

        return list(filter(lambda x: (x.price >= 0.0 and x.price <= 1.0), new_orders))

    def _new_buy_orders(
        self, our_buy_orders: list, our_buy_balance: float, target_price: float
    ):
        """
        Return buy orders which need to be placed to bring total amounts within all buy bands above minimums
        """
        assert isinstance(our_buy_orders, list)
        assert isinstance(our_buy_balance, float)
        assert isinstance(target_price, float)

        new_orders = []
        self.logger.debug("Running new buy orders...")
        for band in self._calculate_virtual_buy_bands(target_price):
            self.logger.debug(band)
            orders = [
                order for order in our_buy_orders if band.includes(order, target_price)
            ]
            total_amount = sum(order.size for order in orders)
            if total_amount < band.min_amount:
                price = math_round_down(band.avg_price(target_price), 2)
                min_size_from_buy_balance = our_buy_balance / price
                size = math_round_down(
                    min(band.avg_amount - total_amount, min_size_from_buy_balance), 2
                )

                if (price > float(0)) and (size > float(0)):
                    self.logger.debug(
                        f"{band} has existing amount {total_amount},"
                        f" creating new buy order with price {price} and size: {size}"
                    )

                    # express size in terms of the USDC needed to place this order
                    size_buy_token = size * price
                    our_buy_balance = our_buy_balance - size_buy_token
                    new_orders.append(Order(size=size, price=price, side=BUY))

        return list(filter(lambda x: (x.price >= 0.0 and x.price <= 1.0), new_orders))

    @staticmethod
    def _bands_overlap(bands: list):
        def two_bands_overlap(band1, band2):
            return (
                band1.min_margin < band2.max_margin
                and band2.min_margin < band1.max_margin
            )

        for band1 in bands:
            if (
                len(list(filter(lambda band2: two_bands_overlap(band1, band2), bands)))
                > 1
            ):
                return True
        return False
