from prometheus_client import Counter, Gauge, Histogram

chain_requests_counter = Counter(
    "requests_counter",
    "Counts the chain executions",
    labelnames=["method", "status"],
    namespace="arbitrage_keeper_chain",
)
keeper_balance_amount = Gauge(
    "balance_amount",
    "Balance of the bot",
    labelnames=["accountaddress", "assetaddress", "tokenid"],
    namespace="arbitrage_keeper_chain",
)
clob_requests_latency = Histogram(
    "clob_requests_latency",
    "Latency of the clob requests",
    labelnames=["method", "status"],
    namespace="arbitrage_keeper_chain",
)
gas_station_latency = Histogram(
    "gas_station_latency",
    "Latency of the gas station",
    labelnames=["strategy", "status"],
    namespace="arbitrage_keeper_chain",
)
