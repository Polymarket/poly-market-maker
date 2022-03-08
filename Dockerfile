FROM python:3.9.10-slim-buster

RUN apt update -y && apt-get install -y python3-dev build-essential

WORKDIR /opt/polymarket

RUN cd /opt/polymarket

COPY poly_market_maker poly_market_maker
COPY Makefile .
COPY requirements.txt .
COPY logging.yaml .
COPY run_keeper.sh .
COPY bands.json .
COPY install.sh .

RUN ./install.sh

# CMD ["./run_keeper.sh"]