#!/bin/bash

## Parameters

BANDS_CONFIG_FILE=$1
TOKEN_ID=$2
ODDS_API_SPORT=$3
ODDS_API_REGION=$4
ODDS_API_MARKET=$5
ODDS_API_MATCH_ID=$6
ODDS_API_TEAM_NAME=$7
IMAGE_ID=$8

echo "Bands file: $BANDS_CONFIG_FILE" # bands file
echo "Token id: $TOKEN_ID" # token id
echo "Sport: $ODDS_API_SPORT" # odds api sport
echo "Region: $ODDS_API_REGION" # odds api region
echo "Market: $ODDS_API_MARKET" # odds api market
echo "Game id: $ODDS_API_MATCH_ID" # match id
echo "Team: $ODDS_API_TEAM_NAME" # team name
echo "Image id: $IMAGE_ID" # ecr image id

## Variable for the file

NAME="mmk-nba-game-$ODDS_API_MATCH_ID"
PORT_NAME="mmk-${NAME:0:10}"


## File creation

K8S_FILE="$NAME.yaml"

cat > $K8S_FILE <<- EOM
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $NAME
spec:
  selector:
    matchLabels:
      app: $NAME
  replicas: 1
  template:
    metadata:
      labels:
        app: $NAME
    spec:
      containers:
        - name: $NAME
          image: 244513468026.dkr.ecr.eu-west-2.amazonaws.com/polymarket:$IMAGE_ID
          command: ["/opt/polymarket/run_keeper.sh"]
          imagePullPolicy: Always
          env:
            - name: PK
              valueFrom:
                secretKeyRef:
                  name: mmk-staging-secrets
                  key: pk
            - name: CHAIN_ID
              value: "80001"
            - name: RPC_URL
              valueFrom:
                secretKeyRef:
                  name: mmk-staging-secrets
                  key: rpc_url
            - name: CLOB_API_URL
              value: https://clob-staging.polymarket.com
            - name: CLOB_API_KEY
              valueFrom:
                secretKeyRef:
                  name: mmk-staging-secrets
                  key: clob_api_key
            - name: CLOB_SECRET
              valueFrom:
                secretKeyRef:
                  name: mmk-staging-secrets
                  key: clob_api_secret
            - name: CLOB_PASS_PHRASE
              valueFrom:
                secretKeyRef:
                  name: mmk-staging-secrets
                  key: clob_api_passphrase
            - name: BANDS_CONFIG_FILE
              value: $BANDS_CONFIG_FILE
            - name: TOKEN_ID
              value: "$TOKEN_ID"
            - name: LOGGING_CONFIG_FILE
              value: "logging.yaml"
            - name: GAS_STRATEGY
              value: "station"
            - name: GAS_STATION_URL
              value: "https://gasstation-mumbai.matic.today/"
            # odds
            - name: ODDS_API_URL
              value: "https://api.the-odds-api.com/v4/sports"
            - name: PRICE_FEED_SOURCE
              value: "odds_api"
            - name: ODDS_API_SPORT
              value: $ODDS_API_SPORT
            - name: ODDS_API_REGION
              value: $ODDS_API_REGION
            - name: ODDS_API_MARKET
              value: $ODDS_API_MARKET
            - name: ODDS_API_MATCH_ID
              value: $ODDS_API_MATCH_ID
            - name: ODDS_API_TEAM_NAME
              value: $ODDS_API_TEAM_NAME
            - name: ODDS_API_KEY
              valueFrom:
                secretKeyRef:
                  name: mmk-staging-secrets
                  key: odds_api_key
          ports:
            - containerPort: 9008
              name: $PORT_NAME
              protocol: TCP
---
apiVersion: v1
kind: Service
metadata:
  name: $NAME
  namespace: default
  annotations:
    prometheus.io/port: "9008"
    prometheus.io/scrape: "true"
    prometheus.io/path: "/"
  labels:
    app: $NAME
spec:
  selector:
    app: $NAME
  ports:
    - port: 9008
      name: $PORT_NAME
      protocol: TCP
      targetPort: 9008
EOM



echo $K8S_FILE