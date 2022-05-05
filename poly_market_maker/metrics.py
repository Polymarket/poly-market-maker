from prometheus_client import Counter, Gauge, Histogram

chain_requests_counter = Counter(
    "chain_requests_counter",
    "Counts the chain executions",
    labelnames=["method", "status"],
    namespace="market_maker",
)
keeper_balance_amount = Gauge(
    "balance_amount",
    "Balance of the bot",
    labelnames=["accountaddress", "assetaddress", "tokenid"],
    namespace="market_maker",
)
clob_requests_latency = Histogram(
    "clob_requests_latency",
    "Latency of the clob requests",
    labelnames=["method", "status"],
    namespace="market_maker",
)
gas_station_latency = Histogram(
    "gas_station_latency",
    "Latency of the gas station",
    labelnames=["strategy", "status"],
    namespace="market_maker",
)
odds_api_latency = Histogram(
    "odds_api_latency",
    "Latency of odds api",
    labelnames=["method", "status"],
    namespace="market_maker",
)
odds_api_remaining_requests = Gauge(
    "odds_api_remaining_requests",
    "Remaining requests for our odds api key",
    namespace="market_maker",
)
