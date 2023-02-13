from unittest import TestCase, mock
from web3 import Web3

from poly_market_maker.fpmm import FPMM
from poly_market_maker.gas import GasStation, GasStrategy
from poly_market_maker.contracts import Contracts


class TestOddsAPI(TestCase):
    def test_get_price(self):
        w3 = Web3(Web3.HTTPProvider(""))
        gas_station = GasStation(strat=GasStrategy("station"), w3=w3)
        contracts = Contracts(w3, gas_station)

        fpmm = FPMM(contracts)

        m = mock.Mock()
        m.side_effect = [100, 300]

        contracts.balance_of_erc1155 = m

        price = fpmm.get_price(
            conditional_token="",
            fpmm="",
            token_id="",
            token_complement_id="",
        )

        self.assertEqual(price, 0.75)
