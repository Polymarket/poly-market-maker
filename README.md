# poly-market-maker

Market maker keeper for the Polymarket CLOB

Requires:

- Python 3.10.10
- virtualenv

## Usage

- Start and activate a virtualenv: `python -m venv .venv && source .venv/bin/activate`

- Install dependencies: `make init`

- Create a `.env` file. See `.env.example`

- Create a `bands.json` configuration file. See the existing `bands.json`

- Start the keeper with `./run_keeper.sh`
