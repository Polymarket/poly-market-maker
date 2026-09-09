import enum
import math
import web3
import requests
import logging
import time

from poly_market_maker.metrics import gas_station_latency

DEFAULT_FIXED_GAS_PRICE = 100000000000

# Seconds to wait for the external gas station before giving up and falling back
# to the configured fixed gas price. Without a timeout `requests.get` inherits
# the socket default of "wait forever": a gas station that accepts the connection
# and then stalls blocks the keeper's whole trading loop indefinitely, because
# every transaction goes through get_gas_price().
GAS_STATION_TIMEOUT_SECONDS = 5


class GasStrategy(enum.Enum):
    FIXED = "fixed"
    STATION = "station"
    WEB3 = "web3"


class GasStation:
    def __init__(
        self,
        strat=GasStrategy.STATION,
        w3: web3.Web3 = None,
        url: str = None,
        fixed=DEFAULT_FIXED_GAS_PRICE,
    ):
        self.strat = self._get_gas_strategy(w3, url, strat)
        self.w3 = w3
        self.url = url
        self.fixed = int(fixed) if fixed else DEFAULT_FIXED_GAS_PRICE
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_gas_price(self) -> int:
        """
        Get gas price.

        Always returns a usable integer. The previous implementation initialised
        `gas = None` and returned it unchanged on any exception, and also left it
        as None whenever `self.strat` matched none of the three branches. Callers
        do not check: `contracts.py` passes the result straight into
        `transact({"gasPrice": self.gas_station.get_gas_price()})`, and web3
        rejects a None gasPrice, so a transient gas-station failure turned into a
        failed transaction instead of a transaction at the fallback price -- which
        is the entire purpose of having a configured fixed price.

        Falling back to `self.fixed` is the same decision the two private helpers
        already make internally; this makes it hold for the WEB3 branch and for
        any future strategy value as well.
        """
        self.logger.info(f"Using gas price strategy: {self.strat.value.upper()}...")
        gas = None
        start_time = time.time()

        try:
            if self.strat == GasStrategy.FIXED:
                gas = self.fixed

            if self.strat == GasStrategy.WEB3:
                # Delegate to the helper rather than calling
                # `self.w3.eth.generate_gas_price()` inline. The inline call left
                # `_get_rpc_gas_price` unreachable, so this branch silently lost
                # both of that helper's behaviours: rounding up to the next gwei
                # (which avoids "transaction underpriced" rejections) and the
                # fallback to the fixed price when the RPC call fails.
                gas = self._get_rpc_gas_price()

            if self.strat == GasStrategy.STATION:
                gas_station_gas_price = self._get_gas_station_gas()
                gas = gas_station_gas_price

            gas_station_latency.labels(strategy=self.strat.value, status="ok").observe(
                (time.time() - start_time)
            )

            self.logger.info(f"Gas: {gas}")
        except Exception as e:
            self.logger.error(
                f"Error fetching gas from gas station, strategy: {self.strat.value.upper()}: {e}"
            )
            gas_station_latency.labels(
                strategy=self.strat.value, status="error"
            ).observe((time.time() - start_time))

        if gas is None:
            self.logger.warning(
                f"No gas price resolved for strategy {self.strat.value.upper()}; "
                f"using configured fixed gas price: {self.fixed}"
            )
            return self.fixed

        return int(gas)

    def _get_gas_strategy(self, w3, url, user_given_strat):
        # if the user provided a strategy, use that directly
        if user_given_strat:
            return user_given_strat

        if url:
            return GasStrategy.STATION

        if w3:
            return GasStrategy.WEB3

        return GasStrategy.FIXED

    def _get_rpc_gas_price(self):
        try:
            gas = self.w3.eth.generate_gas_price()
            # Round up to avoid transaction underpriced errors
            return math.ceil(gas / (10**9)) * (10**9)
        # `except Exception` rather than a bare `except:`. A bare except also
        # catches KeyboardInterrupt and SystemExit, so Ctrl-C during an RPC call
        # was swallowed and reported as a gas-fetch error while the keeper kept
        # trading. The exception is now logged too: `%s` of the cause is what
        # distinguishes a misconfigured RPC endpoint from a transient timeout.
        except Exception as e:
            self.logger.error(
                f"Error fetching gas from web3, returning configured fixed gas price: {self.fixed}: {e}"
            )
            return self.fixed

    def _get_gas_station_gas(self):
        try:
            resp = requests.get(self.url, timeout=GAS_STATION_TIMEOUT_SECONDS)

            # Raise on 4xx/5xx. Without this, an HTML error page parsed as JSON
            # (or a JSON body with no "fast" key) reached `math.ceil(None)`, which
            # raised TypeError here and was reported as a generic gas-fetch
            # failure rather than as the HTTP error it was.
            resp.raise_for_status()

            resp_json = resp.json()

            # Always fast
            gas = resp_json.get("fast")

            if gas is None:
                raise ValueError(
                    f"gas station response from {self.url} has no 'fast' field"
                )

            return math.ceil(gas) * (10**9)
        # See _get_rpc_gas_price for why this is `except Exception` and not a
        # bare `except:`.
        except Exception as e:
            self.logger.error(
                f"Error fetching gas from gasstation, returning configured fixed gas price: {self.fixed}: {e}"
            )
            return self.fixed
