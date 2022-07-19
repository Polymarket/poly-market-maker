#!/bin/bash

## Parameters

BANDS_CONFIG_FILE=$1
TOKEN_ID_TEAM_A=$2
TOKEN_ID_TEAM_B=$3
ODDS_API_SPORT=$4
ODDS_API_REGION=$5
ODDS_API_MARKET=$6
ODDS_API_MATCH_ID=$7
ODDS_API_TEAM_A_NAME=$8
ODDS_API_TEAM_B_NAME=$9
IMAGE_ID="${10}"
ENVIRONMENT="${11}"
BOT="${12}"
PRICE_FEED_SOURCE="${13}"
FPMM_ADDRESS="${14}"

echo "Bands file: $BANDS_CONFIG_FILE" # bands file
echo "Token id team A: $TOKEN_ID_TEAM_A" # token id
echo "Token id team B: $TOKEN_ID_TEAM_B" # token id
echo "Sport: $ODDS_API_SPORT" # odds api sport
echo "Region: $ODDS_API_REGION" # odds api region
echo "Market: $ODDS_API_MARKET" # odds api market
echo "Game id: $ODDS_API_MATCH_ID" # match id
echo "Team A: $ODDS_API_TEAM_A_NAME" # team name
echo "Team B: $ODDS_API_TEAM_B_NAME" # team name
echo "Image id: $IMAGE_ID" # ecr image id
echo "Environment: $ENVIRONMENT" # ecr image id
echo "Group: $GROUP" # group id
echo "Price feed source: $PRICE_FEED_SOURCE" # price feed source
echo "FPMM address: $FPMM_ADDRESS" # fpmm address for pricing

## Variable for the file

NAME_TEAM_A="mmk-game-$ODDS_API_MATCH_ID-team-a"
PORT_NAME_A="${ODDS_API_MATCH_ID:0:11}${ODDS_API_MARKET:0:3}a"

NAME_TEAM_B="mmk-game-$ODDS_API_MATCH_ID-team-b"
PORT_NAME_B="${ODDS_API_MATCH_ID:0:11}${ODDS_API_MARKET:0:3}b"

SECRETS_NAME=""
CHAIN_ID=""
CLOB_API_URL=""
GAS_STATION_URL=""
if [ $ENVIRONMENT = "prod" ]
then
  SECRETS_NAME="mmk-prod-secrets"
  CHAIN_ID="137"
  CLOB_API_URL="https://clob.polymarket.com"
  GAS_STATION_URL="https://gasstation-mainnet.matic.network/v1/"
else
  SECRETS_NAME="mmk-staging-secrets"
  CHAIN_ID="80001"
  CLOB_API_URL="https://clob-staging.polymarket.com"
  GAS_STATION_URL="https://gasstation-mumbai.matic.today/"
fi

echo "Secrets name: $SECRETS_NAME" # name of the secret
echo "Chain: $CHAIN_ID" # chain id
echo "Clob url: $CLOB_API_URL" # clob tracker api url
echo "Gas station url: $GAS_STATION_URL" # gas station url

## File creation

K8S_FILE_A="$NAME_TEAM_A.yaml"
cat > $K8S_FILE_A <<- EOM
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $NAME_TEAM_A
spec:
  selector:
    matchLabels:
      app: $NAME_TEAM_A
  replicas: 1
  template:
    metadata:
      labels:
        app: $NAME_TEAM_A
    spec:
      containers:
        - name: $NAME_TEAM_A
          image: 244513468026.dkr.ecr.eu-west-2.amazonaws.com/polymarket:$IMAGE_ID
          command: ["/opt/polymarket/run_keeper.sh"]
          imagePullPolicy: Always
          env:
            - name: PK
              valueFrom:
                secretKeyRef:
                  name: $SECRETS_NAME
                  key: team_${GROUP}_a_pk
            - name: CHAIN_ID
              value: "$CHAIN_ID"
            - name: RPC_URL
              valueFrom:
                secretKeyRef:
                  name: $SECRETS_NAME
                  key: rpc_url
            - name: CLOB_API_URL
              value: $CLOB_API_URL
            - name: CLOB_API_KEY
              valueFrom:
                secretKeyRef:
                  name: $SECRETS_NAME
                  key: clob_api_key
            - name: CLOB_SECRET
              valueFrom:
                secretKeyRef:
                  name: $SECRETS_NAME
                  key: clob_api_secret
            - name: CLOB_PASS_PHRASE
              valueFrom:
                secretKeyRef:
                  name: $SECRETS_NAME
                  key: clob_api_passphrase
            - name: BANDS_CONFIG_FILE
              value: $BANDS_CONFIG_FILE
            - name: TOKEN_ID
              value: "$TOKEN_ID_TEAM_A"
            - name: LOGGING_CONFIG_FILE
              value: "logging.yaml"
            - name: GAS_STRATEGY
              value: "station"
            - name: GAS_STATION_URL
              value: $GAS_STATION_URL
            # odds
            - name: ODDS_API_URL
              value: "https://api.the-odds-api.com/v4/sports"
            - name: PRICE_FEED_SOURCE
              value: $PRICE_FEED_SOURCE
            - name: ODDS_API_SPORT
              value: $ODDS_API_SPORT
            - name: ODDS_API_REGION
              value: $ODDS_API_REGION
            - name: ODDS_API_MARKET
              value: $ODDS_API_MARKET
            - name: ODDS_API_MATCH_ID
              value: $ODDS_API_MATCH_ID
            - name: ODDS_API_TEAM_NAME
              value: "$ODDS_API_TEAM_A_NAME"
            - name: ODDS_API_KEY
              valueFrom:
                secretKeyRef:
                  name: $SECRETS_NAME
                  key: odds_api_key
            - name: COMPLEMENT_ID
              value: "$TOKEN_ID_TEAM_B"
            - name: FPMM_ADDRESS
              value: $FPMM_ADDRESS
          ports:
            - containerPort: 9008
              name: $PORT_NAME_A
              protocol: TCP
---
apiVersion: v1
kind: Service
metadata:
  name: $NAME_TEAM_A
  namespace: default
  annotations:
    prometheus.io/port: "9008"
    prometheus.io/scrape: "true"
    prometheus.io/path: "/"
  labels:
    app: $NAME_TEAM_A
spec:
  selector:
    app: $NAME_TEAM_A
  ports:
    - port: 9008
      name: $PORT_NAME_A
      protocol: TCP
      targetPort: 9008
EOM


K8S_FILE_B="$NAME_TEAM_B.yaml"
cat > $K8S_FILE_B <<- EOM
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $NAME_TEAM_B
spec:
  selector:
    matchLabels:
      app: $NAME_TEAM_B
  replicas: 1
  template:
    metadata:
      labels:
        app: $NAME_TEAM_B
    spec:
      containers:
        - name: $NAME_TEAM_B
          image: 244513468026.dkr.ecr.eu-west-2.amazonaws.com/polymarket:$IMAGE_ID
          command: ["/opt/polymarket/run_keeper.sh"]
          imagePullPolicy: Always
          env:
            - name: PK
              valueFrom:
                secretKeyRef:
                  name: $SECRETS_NAME
                  key: team_${GROUP}_b_pk
            - name: CHAIN_ID
              value: "$CHAIN_ID"
            - name: RPC_URL
              valueFrom:
                secretKeyRef:
                  name: $SECRETS_NAME
                  key: rpc_url
            - name: CLOB_API_URL
              value: $CLOB_API_URL
            - name: CLOB_API_KEY
              valueFrom:
                secretKeyRef:
                  name: $SECRETS_NAME
                  key: clob_api_key
            - name: CLOB_SECRET
              valueFrom:
                secretKeyRef:
                  name: $SECRETS_NAME
                  key: clob_api_secret
            - name: CLOB_PASS_PHRASE
              valueFrom:
                secretKeyRef:
                  name: $SECRETS_NAME
                  key: clob_api_passphrase
            - name: BANDS_CONFIG_FILE
              value: $BANDS_CONFIG_FILE
            - name: TOKEN_ID
              value: "$TOKEN_ID_TEAM_B"
            - name: LOGGING_CONFIG_FILE
              value: "logging.yaml"
            - name: GAS_STRATEGY
              value: "station"
            - name: GAS_STATION_URL
              value: $GAS_STATION_URL
            # odds
            - name: ODDS_API_URL
              value: "https://api.the-odds-api.com/v4/sports"
            - name: PRICE_FEED_SOURCE
              value: $PRICE_FEED_SOURCE
            - name: ODDS_API_SPORT
              value: $ODDS_API_SPORT
            - name: ODDS_API_REGION
              value: $ODDS_API_REGION
            - name: ODDS_API_MARKET
              value: $ODDS_API_MARKET
            - name: ODDS_API_MATCH_ID
              value: $ODDS_API_MATCH_ID
            - name: ODDS_API_TEAM_NAME
              value: "$ODDS_API_TEAM_B_NAME"
            - name: ODDS_API_KEY
              valueFrom:
                secretKeyRef:
                  name: $SECRETS_NAME
                  key: odds_api_key
            - name: COMPLEMENT_ID
              value: "$TOKEN_ID_TEAM_A"
            - name: FPMM_ADDRESS
              value: $FPMM_ADDRESS
          ports:
            - containerPort: 9008
              name: $PORT_NAME_B
              protocol: TCP
---
apiVersion: v1
kind: Service
metadata:
  name: $NAME_TEAM_B
  namespace: default
  annotations:
    prometheus.io/port: "9008"
    prometheus.io/scrape: "true"
    prometheus.io/path: "/"
  labels:
    app: $NAME_TEAM_B
spec:
  selector:
    app: $NAME_TEAM_B
  ports:
    - port: 9008
      name: $PORT_NAME_B
      protocol: TCP
      targetPort: 9008
EOM



echo $K8S_FILE_A
echo $K8S_FILE_B