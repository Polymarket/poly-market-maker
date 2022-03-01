#!/usr/bin/env bash

echo "Running poly-market-maker-keeper..."

source .venv/bin/activate || exit

source .env

exec python3 -m poly_market_maker.market_maker \
--chain-id $CHAIN_ID \
--eth-key $PK \
--rpc-url $RPC_URL \
--clob-api-url $CLOB_API_URL \
--clob-api-key $CLOB_API_KEY \
--clob-api-secret $CLOB_SECRET \
--clob-api-passphrase $CLOB_PASS_PHRASE \
--config $BANDS_CONFIG_FILE \
--token-id $TOKEN_ID \

