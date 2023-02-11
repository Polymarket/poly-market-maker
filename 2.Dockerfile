FROM python:3.10.10-slim-buster


RUN groupadd -r keeper && useradd --no-log-init -r -g keeper keeper

WORKDIR /opt/keeper

COPY poly_market_maker poly_market_maker
COPY Makefile .
COPY requirements.txt .
COPY logging.yaml .
COPY run_keeper.sh .
COPY bands.json .
COPY loose_small.json .
COPY loose_large.json .
COPY tight_small.json .
COPY tight_large.json .
COPY install.sh .

RUN ./install.sh

CMD ["./run_keeper.sh"]