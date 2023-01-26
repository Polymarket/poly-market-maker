#!/usr/bin/env bash

echo "Running poly-market-maker-keeper..."

if [ -f .env ]; then
    echo "Sourcing env variables from dot env file..."
    source .env
else
    echo "Fetching env variables.."
fi

source .venv/bin/activate

exec python3 -m poly_market_maker.market_maker \
    --chain-id "$CHAIN_ID" \
    --private-key "$PRIVATE_KEY" \
    --rpc-url "$RPC_URL" \
    --clob-api-url "$CLOB_API_URL" \
    --clob-api-key "$CLOB_API_KEY" \
    --clob-api-secret "$CLOB_SECRET" \
    --clob-api-passphrase "$CLOB_PASS_PHRASE" \
    --bands-config "$BANDS_CONFIG_FILE" \
    --condition-id "$CONDITION_ID" \
    --token-id-A "$TOKEN_ID_A" \
    --token-id-B "$TOKEN_ID_B"

# --gas-strategy $GAS_STRATEGY \
# --gas-station-url $GAS_STATION_URL \
# --price-feed-source $PRICE_FEED_SOURCE \
# --odds-api-url $ODDS_API_URL \
# --odds-api-key $ODDS_API_KEY \
# --odds-api-sport $ODDS_API_SPORT \
# --odds-api-region $ODDS_API_REGION \
# --odds-api-market $ODDS_API_MARKET \
# --odds-api-match-id $ODDS_API_MATCH_ID \
# --odds-api-team-name "$ODDS_API_TEAM_NAME" \
# --fpmm-address "$FPMM_ADDRESS" \
# --complement-id "$COMPLEMENT_ID"
