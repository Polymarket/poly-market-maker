#!/usr/bin/env bash

echo "Running poly-market-maker-keeper..."

if [ -f .env ]
then
    echo "Sourcing env variables from dot env file..."
    source .env
else
    echo "Fetching env variables.."
fi

source .venv/bin/activate

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
--gas-strategy $GAS_STRATEGY \
--gas-station-url $GAS_STATION_URL \

