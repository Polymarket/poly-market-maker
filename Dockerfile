FROM python:3.10.10-slim-buster

WORKDIR /opt/keeper

RUN apt update -y && apt-get install -y python3-dev build-essential
RUN groupadd -r keeper && useradd -r -g keeper keeper
RUN chown -R keeper:keeper /opt/keeper

COPY poly_market_maker poly_market_maker
COPY requirements.txt .
COPY logging.yaml .

COPY bands.json .
COPY loose_small.json .
COPY loose_large.json .
COPY tight_small.json .
COPY tight_large.json .
COPY install.sh .
COPY run_keeper.sh .

RUN ./install.sh
USER keeper