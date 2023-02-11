FROM python:3.10.10-slim-buster

# RUN apt update -y && apt-get install -y python3-dev build-essential

WORKDIR /opt/polymarket

COPY poly_market_maker poly_market_maker
COPY requirements.txt .
COPY logging.yaml .

COPY bands.json .
COPY loose_small.json .
COPY loose_large.json .
COPY tight_small.json .
COPY tight_large.json .
COPY install.sh .

RUN ./install.sh

# CMD ["./run_keeper.sh"]