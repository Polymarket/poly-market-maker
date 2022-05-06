
import json
from unittest import TestCase, mock

from poly_market_maker.odds_api import OddsAPI


class TestOddsAPI(TestCase):
    def test_get_price(self):
      odds_api = OddsAPI(
        api_key='api_key',
        sport="sport",
        region="region",
        market="market",
      )

      with open("./tests/odds_response.json") as odr:
          odds_response = json.load(odr)

      odds_api.get_odds = mock.Mock(return_value=odds_response)

      price = odds_api.get_price(
        match_id = "271cf1e73a4e2caa33331ef15ace8bc1",
        team_name = "Philadelphia 76ers"
      )

      self.assertEqual(price, 0.5030381348009277)

