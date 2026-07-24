# poly-market-maker

Market maker keeper for the Polymarket CLOB.

## NOTE

This software is experimental and in active development.
Use at your own risk.

## Description

The keeper is an automated market maker for CLOB markets.
Places and cancels orders to keep open orders near the midpoint price according to one of two strategies.

## Requirements
> **Note:** This market maker trades directly with an EOA (Externally Owned Account) private key. Proxy wallet / deposit wallet accounts (those created via the Polymarket web UI, Magic.link, or Privy) are **not supported**. You must use a standard EOA private key. See [#79](https://github.com/Polymarket/poly-market-maker/issues/79) for context.


- Python 3.10

## Setup

- Run `./install.sh` to set up the virtual environment and install depedencies.

- Create a `.env` file. See `.env.example`.

- Modify the entries in `config.env`.

- Modify the corresponding strategy config in `./config`, if desired.

## Usage

- Start the keeper with `./run-local.sh`.

### Usage with Docker

- To start the keeper with docker, run `docker compose up`.

## Config

The `config.env` file defines 3 environment variables:

- `CONDITION_ID`, the condition id of the market in hex string format.
- `STRATEGY`, the strategy to use, either "Bands" or "AMM" (case insensitive)
- `CONFIG`, the path to the strategy config file.

## Strategies

- [Amm](./docs/strategies/amm.md)
- [Bands](./docs/strategies/bands.md)

### Strategy Lifecycle

Every `sync_interval` (the default is 30s), the strategies do the following:

1. Fetch the current midpoint price from the CLOB
2. Compute expected orders.
3. Compare expected orders to open orders.
4. Compute open orders to cancel and new orders to place to achieve or approximate the expected orders.
5. Cancel orders.
6. Place new orders.

When the app receives a SIGTERM, all orders are cancelled and the app exits gracefully.
