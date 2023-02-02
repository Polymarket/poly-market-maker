import math

X = 500
Y = 1000
Pa = 0.7
Pb = 1 - Pa
Pmin = 0
Pmax = 0.95
Delta = 0.05
PminA = 0.05
PminB = 0.05

# 1. Get order sizes from orderbook
# 2. Compute available funds
# 3. Cancel all orders
# 4. Place new orders


def sell_size(x, pmin, pmax, pf):
    L = sell_liquidity(x, pmin, pmax)
    a = L / math.sqrt(pmax) - L / math.sqrt(pf) + x
    return a


def sell_cost(x, pmin, pmax, pf):
    L = sell_liquidity(x, pmin, pmax)
    b = L * math.sqrt(pf) - L * math.sqrt(pmin)
    return b


def buy_size(y, pmin, pmax, pf):
    L = buy_liquidity(y, pmin, pmax)
    a = L / math.sqrt(pf) - L / math.sqrt(pmax)
    return a


def buy_cost(y, pmin, pmax, pf):
    L = buy_liquidity(y, pmin, pmax)
    b = y + L * math.sqrt(pmin) - L * math.sqrt(pf)
    return b


def sell_liquidity(x, pmin, pmax):
    L = x / (1 / math.sqrt(pmin) - 1 / math.sqrt(pmax))
    return L


def buy_liquidity(y, pmin, pmax):
    L = y / (math.sqrt(pmax) - math.sqrt(pmin))
    return L


def phi(p, pmin, delta):
    return (1 / (math.sqrt(p) - math.sqrt(pmin))) * (
        1 / math.sqrt(p - delta) - 1 / math.sqrt(p)
    )


def buy_liq_A(ya, pa, pminA, pminB, delta, sell_a, sell_b):
    return (sell_a - sell_b + ya * phi(1 - pa, pminB, delta)) / (
        phi(pa, pminA, delta) + phi(1 - pa, pminB, delta)
    )


Ya = buy_liq_A(Y, Pa, PminA, PminB, Delta, 0, 0)
Yb = Y - Ya


def buy_diff(arr):
    return [
        arr[i] if i == len(arr) - 1 else arr[i] - arr[i + 1]
        for i in range(len(arr))
    ]


print(Ya, Yb)


buy_prices_a = [
    float(p / 100)
    for p in range(int(PminA * 100), int(Pa * 100), int(Delta * 100))
]
buy_sizes_a = buy_diff([buy_size(Ya, PminA, Pa, Pf) for Pf in buy_prices_a])
buy_costs_a = [
    price * size for (price, size) in zip(buy_prices_a, buy_sizes_a)
]

buy_prices_b = [
    float(p / 100)
    for p in range(int(PminB * 100), int(Pb * 100), int(Delta * 100))
]
buy_sizes_b = buy_diff([buy_size(Yb, PminB, Pb, Pf) for Pf in buy_prices_b])
buy_costs_b = (
    price * size for (price, size) in zip(buy_prices_b, buy_sizes_b)
)

# convert b to a sales
# sizes are the same
# costs are ?

sell_prices = [1 - price for price in buy_prices_b][::-1]
sell_sizes = buy_sizes_b[::-1]
sell_costs = [
    (1 - price) * size for (price, size) in zip(sell_prices, sell_sizes)
]


prices = buy_prices_a + [Pa] + sell_prices
costs = buy_costs_a + [0] + sell_costs
sizes = buy_sizes_a + [0] + sell_sizes
