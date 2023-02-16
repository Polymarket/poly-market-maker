# poly-market-maker

Market maker keeper for the Polymarket CLOB.

## Requirements

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

- [AMM](./docs/strategies/amm.md)
- [BANDS](./docs/strategies/bands.md)
