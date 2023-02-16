# Bands

## Config

```[python]
{
    minMargin,
    avgMargin,
    maxMargin,
    minSize,
    avgSize,
    maxSize
}
```

When given a target price, the strategy ensures that net size of all orders within the band is in the range [minSize, maxSize].
Due to the binary nature of the order book, buy orders for $\text{TokenA}$ are equivalent from a liquidity perspective to sell orders for $\text{TokenB}$ with the same size and complementary price.

For each band, given a target price $\text{targetPrice}$, a $\text{minPrice}$ and $\text{maxPrice}$ are computed as follows:

### Buy orders:

$$
\begin{align*}
\text{minPrice} &= \text{targetPrice} - \text{minMargin}, \text{ and} \\
\text{maxPrice} &= \text{targetPrice} - \text{maxMargin}.
\end{align*}
$$

### Sell orders:

$$
\begin{align*}
\text{minPrice} &= \text{targetPrice} + \text{minMargin}, \text{ and} \\
\text{maxPrice} &= \text{targetPrice} + \text{maxMargin}.
\end{align*}
$$

There are two sets of bands: one for buy orders for $\text{TokenA}$ and sell orders for $\text{TokenB}$, and another for buy orders for $\text{TokenB}$ and sell orders for $\text{TokenA}$.
