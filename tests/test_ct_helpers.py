from unittest import TestCase

from poly_market_maker.ct_helpers import CTHelpers

class TestCTHelpers(TestCase):
    def test_get_token_id(self):
        usdc_address = '0x2E8DCfE708D44ae2e406a1c02DFE2Fa13012f961'
        condition_id = "0xbd31dc8a20211944f6b70f31557f1001557b59905b7738480ca09bd4532f84af"
        token_id_0=1343197538147866997676250008839231694243646439454152539053893078719042421992
        token_id_1=16678291189211314787145083999015737376658799626183230671758641503291735614088

        self.assertEqual(CTHelpers.get_token_id(condition_id, usdc_address, 0), token_id_0)
        self.assertEqual(CTHelpers.get_token_id(condition_id, usdc_address, 1), token_id_1)

