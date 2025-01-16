# poly-market-maker

Automated market maker keeper for the Polymarket CLOB (Centralized Limit Order Book).

## Overview

This keeper is designed to automate market making strategies on Polymarket's CLOB markets. It continuously monitors market conditions and manages orders to maintain liquidity near the midpoint price using sophisticated trading strategies.

## ⚠️ Disclaimer

This software is experimental and in active development.
Use at your own risk. Please ensure you understand the trading strategies and risks involved before deployment.

## Features

- Automated order placement and cancellation
- Multiple trading strategies support (Bands and AMM)
- Real-time market monitoring
- Graceful shutdown with order cancellation
- Docker support for easy deployment

## Technical Requirements

- Python ≤ 3.10 (versions up to 3.10 due to dependency constraints)
- Active Polymarket account with API access

### Optional Requirements
- Docker and Docker Compose (for containerized deployment)

## Installation

### Standard Setup

1. Clone the repository:
```bash
git clone https://github.com/username/poly-market-maker.git
cd poly-market-maker
```

2. Run the installation script:
```bash
./install.sh
```

3. Configure your environment:
   - Copy `.env.example` to `.env`
   - Update the variables in `.env`
   - Modify `config.env` with your settings

### Docker Setup

1. Ensure Docker and Docker Compose are installed
2. Configure environment files as mentioned above
3. Build and run using Docker Compose

## Configuration

### Environment Variables

Required variables in `config.env`:

- `CONDITION_ID`: Hex string format market condition identifier
- `STRATEGY`: Trading strategy selection ("Bands" or "AMM")
- `CONFIG`: Path to strategy configuration file

## Available Strategies

### AMM Strategy
- Automated Market Making with dynamic pricing
- [Detailed AMM Documentation](./docs/strategies/amm.md)

### Bands Strategy
- Price band-based market making
- [Detailed Bands Documentation](./docs/strategies/bands.md)

## Operation

### Starting the Keeper

Standard mode:
```bash
./run-local.sh
```

Docker mode:
```bash
docker compose up
```

### Strategy Operation Cycle

The keeper operates on a configurable cycle (default: 30 seconds) with the following steps:

1. Market price discovery
2. Order calculation
3. Current position analysis
4. Order optimization
5. Order cancellation
6. New order placement

### Monitoring and Maintenance

- The keeper logs important events and trading activities
- Graceful shutdown is triggered by SIGTERM
- All open orders are automatically cancelled on shutdown

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE.txt](LICENSE.txt) file for details.
