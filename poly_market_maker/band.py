import itertools
import logging

from .utils import math_round_down, math_round_up

from .constants import BUY, SELL, MIN_TICK, A, B
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

        self.type = type

    def excessive_orders(
        self,
        orders: list,
        target_price: float,
        is_first_band: bool,
        is_last_band: bool,
    ):
        """Return orders which need to be cancelled to bring the total order amount in the band below maximum."""
        self.logger.debug(f"Running excessive orders for {self.type()}")
        # Get all orders which are currently present in the band.
        orders_in_band = [
            order for order in orders if self.includes(order, target_price)
        ]
        orders_total_size = sum(order.size for order in orders_in_band)

        # The sorting in which we remove orders depends on which band we are in.
        # * In the first band we start cancelling with orders closest to the target price.
        # * In the last band we start cancelling with orders furthest from the target price.
        # * In remaining cases we remove orders starting from the smallest one.

        def price_sorting(order):
            return abs(order.price - target_price)

        def size_sorting(order):
            return order.size

        if is_first_band:
            sorting = price_sorting
            reverse = True
        elif is_last_band:
            sorting = price_sorting
            reverse = False
        else:
            sorting = size_sorting
            reverse = True

        orders_in_band = sorted(orders_in_band, key=sorting, reverse=reverse)
        buys_in_band = [order for order in orders_in_band if order.side == BUY]
        sells_in_band = [
            order for order in orders_in_band if order.side == SELL
        ]

        buys_in_band_total_size = sum(order.size for order in buys_in_band)
        sells_in_band_total_size = sum(order.size for order in sells_in_band)

        while (
            sells_in_band_total_size > 0
            and sells_in_band_total_size + buys_in_band_total_size
            > self.max_amount
        ):
            sells_in_band.pop()
            sells_in_band_total_size = sum(
                order.size for order in sells_in_band
            )

        while buys_in_band_total_size > self.max_amount:
            buys_in_band.pop()
            buys_in_band_total_size = sum(order.size for order in buys_in_band)

        result = set(orders_in_band) - set(buys_in_band) - set(sells_in_band)
        if len(result) > 0:
            self.logger.info(
                f"{self.type().capitalize()} band (spread <{self.min_margin}, {self.max_margin}>,"
                f" amount <{self.min_amount}, {self.max_amount}>) has amount {orders_total_size}, scheduling"
                f" {len(result)} order(s) for cancellation: {', '.join(map(lambda o: '#' + str(o.id), result))}"
            )

        return result

    def includes(self, order, target_price: float) -> bool:
        # For Buys, the min_margin will produce the price_max
        # E.g target=0.5, min_margin=0.01 = 0.5 * (1- 0.01) = 0.495
        #     target=0.5, max_margin=0.20 = 0.5 * (1- 0.2) = 0.4
        # self.logger.info(f"Included in band check...")
        # self.logger.info(f"target_price: {target_price}")
        # self.logger.info(f"min_margin: {self.min_margin}")
        # self.logger.info(f"max_margin: {self.max_margin}")
        price_max = round(self._apply_margin(target_price, self.min_margin), 2)
        price_min = round(self._apply_margin(target_price, self.max_margin), 2)
        # self.logger.info(f"price_min: {price_min}")
        # self.logger.info(f"price_max: {price_max}")

        included = (order.price <= price_max) and (order.price > price_min)
        # self.logger.info(f"{order} is included in band: {self}?: {included}")
        return included

    def avg_price(self, target_price: float) -> float:
        return self._apply_margin(target_price, self.avg_margin)

    @staticmethod
    def _apply_margin(price: float, margin: float) -> float:
        # absolute margins
        return price - margin

    def __repr__(self):
        return f"Band[type={self.type()}, spread<{self.min_margin}, {self.max_margin}>, amount<{self.min_amount}, {self.max_amount}>]"

    def __str__(self):
        return self.__repr__()


class Bands:
    @staticmethod
    def read(config: dict):
        assert isinstance(config, dict)

        try:
            bands = list(map(Band, config["bands"]))
            bands = list(map(Band, config["bands"]))

        except Exception as e:
            logging.getLogger().exception(
                f"Config file is invalid ({e}). Treating the config file as it has no bands."
            )

            bands = []

        return Bands(bands=bands)

    def __init__(self, bands: list):
        self.logger = logging.getLogger(self.__class__.__name__)
        assert isinstance(bands, list)

        self.bands = bands

        if self._bands_overlap(self.bands):
            self.logger.error("Bands in the config file overlap!")
            raise Exception("Bands in the config file overlap!")

    @staticmethod
    def _derive_band(
        price: float,
        min_price: float,
        avg_price: float,
        max_price: float,
        min_amount: float,
        avg_amount: float,
        max_amount: float,
    ) -> Band:
        # take price and buy target prices and return corresponding margins

        return Band(
            {
                "minMargin": price - max_price,
                "avgMargin": price - avg_price,
                "maxMargin": price - min_price,
                "minAmount": min_amount,
                "avgAmount": avg_amount,
                "maxAmount": max_amount,
            }
        )

    def _calculate_virtual_bands(self, price: float) -> list:
        # take bands and spread orders if they are too tight together
        # if price is .5 and there are two bands -> [min_margin, avg_margin, max_margin)
        # [0.0, 0.001, 0.002) and [0.002, 0.003, 0.004)
        # if we placed orders at these bands without adjustment we would place two orders @.5
        # which would create issues (crossing book and can't associate orders to bands)
        # so we adjust these bands so that we place two orders in the tightest band possible with tick
        # so our orders should be .51 and .52 and our bands become
        # [0.02, 0.02, 0.04) and [0.04, 0.04, 0.06)
        # also make remove bands that would result in orders with price <= 0 or price >= 1.0
        if price <= 0.0:
            return []
        # min_price = 1.0
        # avg_price = 1.0
        # max_price = 1.0
        virtual_bands = []
        for band in self.bands:
            band_min_price = price - band.max_margin
            # band_avg_price = price - band.avg_margin
            # band_max_price = price - band.min_margin

            # note: need to decide what to do here

            # if the bands min price is not positive, skip
            if band_min_price > 0.0:
                virtual_bands.append(band)

            # while band_min_price <= 0.0:
            #     band_min_price += MIN_TICK
            #     band_avg_price += MIN_TICK

            #     virtual_bands.append(band)

            # while band_max_price > min_price:
            #     band_min_price -= MIN_TICK
            #     band_avg_price -= MIN_TICK
            #     band_max_price -= MIN_TICK
            # if band_avg_price == band_min_price:
            #     band_min_price -= MIN_TICK
            # min_price = band_min_price
            # # avg_price = band_avg_price
            # # max_price = band_max_price
            # virtual_buy_bands.append(
            #     self._derive_buy_band(
            #         price,
            #         band_min_price,
            #         band_avg_price,
            #         band_max_price,
            #         band.min_amount,
            #         band.avg_amount,
            #         band.max_amount,
            #     )
            # )

        return virtual_bands

    def _excessive_orders(
        self, orders: list, bands: list, target_price: float
    ):
        """Return orders which need to be cancelled to bring total amounts within all bands below maximums."""
        assert isinstance(orders, list)
        assert isinstance(bands, list)
        assert isinstance(target_price, float)

        for band in bands:
            for order in band.excessive_orders(
                orders,
                target_price,
                band == bands[0],
                band == bands[-1],
            ):
                yield order

    def _outside_any_band_orders(
        self, orders: list, bands: list, target_price: float
    ):
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

    def cancellable_orders(  # here
        self, orders: list, target_price: float
    ) -> list:
        assert isinstance(orders, list)
        assert isinstance(target_price, float)

        if target_price is None:
            self.logger.debug(
                "Cancelling all orders as no price is available."
            )
            orders_to_cancel = orders

        else:
            orders_to_cancel = list(
                itertools.chain(
                    self._excessive_orders(
                        orders,
                        self._calculate_virtual_bands(target_price),
                        target_price,
                    ),
                    self._outside_any_band_orders(
                        orders,
                        self._calculate_virtual_bands(target_price),
                        target_price,
                    ),
                )
            )

        return orders_to_cancel

    def new_orders(  # here
        self,
        orders: list,
        collateral_balance: float,
        token_balance: float,
        target_price: float,
    ) -> list:
        assert isinstance(orders, list)
        assert isinstance(collateral_balance, float)
        assert isinstance(target_price, float)

        if target_price is not None:

            new_sell_orders = (
                self._new_sell_orders(orders, token_balance, target_price)
                if target_price is not None
                else ([], float(0))
            )
            new_buy_orders = (
                self._new_buy_orders(orders, collateral_balance, target_price)
                if target_price is not None
                else ([], float(0))
            )

            return new_buy_orders + new_sell_orders

        else:
            return []

    def _new_sell_orders(
        self,
        sell_orders: list,
        token_balance: float,
        target_price: float,
    ):
        """
        Return sell orders which need to be placed to bring total amounts within all sell bands above minimums
        """
        assert isinstance(sell_orders, list)
        assert isinstance(token_balance, float)
        assert isinstance(target_price, float)

        new_orders = []

        for band in self._calculate_virtual_sell_bands(target_price):
            orders = [
                order
                for order in sell_orders
                if band.includes(order, target_price)
            ]
            total_amount = sum(order.size for order in orders)
            if total_amount < band.min_amount:
                price = band.avg_price(target_price)
                size = min(band.avg_amount - total_amount, token_balance)
                if (
                    (price > float(0))
                    and (price < float(1.0))
                    and (size >= float(15.0))
                ):  # min order size
                    self.logger.debug(
                        f"{band} has existing amount {total_amount},"
                        f" creating new sell order with price {price} and size: {size}"
                    )

                    token_balance -= size
                    new_orders.append(Order(price=price, size=size, side=SELL))

        # what's this ??
        return list(
            filter(lambda x: (x.price >= 0.0 and x.price <= 0.95), new_orders)
        )

    def _new_buy_orders(
        self,
        buy_orders: list,
        collateral_balance: float,
        target_price: float,
    ):
        """
        Return buy orders which need to be placed to bring total amounts within all buy bands above minimums
        """
        assert isinstance(buy_orders, list)
        assert isinstance(collateral_balance, float)
        assert isinstance(target_price, float)

        new_orders = []
        self.logger.debug("Running new buy orders...")
        for band in self._calculate_virtual_bands(target_price):
            self.logger.debug(band)
            orders = [
                order
                for order in buy_orders
                if band.includes(order, target_price)
            ]
            band_size = sum(order.size for order in orders)
            if band_size < band.min_amount:
                price = band.avg_price(target_price)
                size_available = collateral_balance / price
                size = min(
                    band.avg_amount - band_size,
                    size_available,
                )

                if (
                    (price > float(0))
                    and (price < float(1.0))
                    and (size >= float(15.0))
                ):  # min order size
                    self.logger.debug(
                        f"{band} has existing amount {band_size},"
                        f" creating new buy order with price {price} and size: {size}"
                    )

                    collateral_balance -= size * price
                    new_orders.append(Order(size=size, price=price, side=BUY))

        return list(
            filter(lambda x: (x.price >= 0.05 and x.price <= 1.0), new_orders)
        )

    @staticmethod
    def _bands_overlap(bands: list):
        def two_bands_overlap(band1, band2):
            return (
                band1.min_margin < band2.max_margin
                and band2.min_margin < band1.max_margin
            )

        for band1 in bands:
            if (
                len(
                    list(
                        filter(
                            lambda band2: two_bands_overlap(band1, band2),
                            bands,
                        )
                    )
                )
                > 1
            ):
                return True
        return False
