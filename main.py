"""Forecast Bitcoin's US-dollar price 240 minutes ahead.

Standard-library-only implementation conforming to btc-cent-forecast-01 rules.
"""

import json
import math
import os
import sys

MIN_PRICE = 0.00001
MAX_PRICE = 9_999_999.99999
DEFAULT_PRICE = 50_000.0


def price5(val: float) -> float:
    """Clamp price to valid grid range and round to 5 decimal places."""
    clamped = max(MIN_PRICE, min(MAX_PRICE, float(val)))
    rounded = round(clamped, 5)
    return max(MIN_PRICE, min(MAX_PRICE, rounded))


def forecast_case(data: dict, case_id: str) -> float:
    """Compute the 4-hour forecast from minute prices using fitted dislocation/momentum model."""
    if not isinstance(data, dict):
        return DEFAULT_PRICE
    markets = data.get("markets")
    if not isinstance(markets, list) or len(markets) == 0:
        return DEFAULT_PRICE
    m0 = markets[0]
    if not isinstance(m0, dict):
        return DEFAULT_PRICE
    prices = m0.get("prices")
    if not isinstance(prices, list) or len(prices) == 0:
        return DEFAULT_PRICE

    # Fallback price: last valid close
    try:
        last_val = float(prices[-1])
        if math.isfinite(last_val) and last_val > 0:
            fallback = price5(last_val)
        else:
            fallback = DEFAULT_PRICE
    except Exception:
        fallback = DEFAULT_PRICE

    try:
        x = float(prices[-1])
        if not math.isfinite(x) or x <= 0:
            return fallback

        # 4-hour arithmetic mean of last min(240, len(prices)) closes
        k = min(240, len(prices))
        m4h = math.fsum(float(p) for p in prices[-k:]) / k
        if not math.isfinite(m4h) or m4h <= 0:
            return fallback

        # Close 24 hours (1440 minutes) before checkpoint, or first close
        y24_raw = prices[-1441] if len(prices) > 1440 else prices[0]
        y24 = float(y24_raw)
        if not math.isfinite(y24) or y24 <= 0:
            return fallback

        # Fitted dislocation and momentum features:
        # dev measures dislocation from 4-hour mean level; mom measures 24-hour momentum.
        # Fitted parameters: adj = -0.12 * dev - 0.12 * mom, clamped to [-0.06, +0.06].
        dev = math.log(x / m4h)
        mom = math.log(x / y24)
        adj = -0.12 * dev - 0.12 * mom
        adj = max(-0.06, min(0.06, adj))

        price = x * math.exp(adj)
        if not math.isfinite(price):
            return fallback

        return price5(price)
    except Exception:
        return fallback


def main() -> None:
    input_dir = os.environ.get("MAKEFUN_INPUT_DIR") or "/input"
    output_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"

    try:
        os.makedirs(output_dir, exist_ok=True)
    except Exception:
        pass

    try:
        files = sorted(f for f in os.listdir(input_dir) if f.endswith(".in"))
    except Exception:
        files = []

    for filename in files:
        case_id = filename[:-3]
        in_path = os.path.join(input_dir, filename)
        out_path = os.path.join(output_dir, f"{case_id}.out")

        price = DEFAULT_PRICE
        try:
            with open(in_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            price = forecast_case(data, case_id)
        except Exception:
            price = DEFAULT_PRICE

        payload = json.dumps({"forecasts": [{"case": case_id, "price": price}]}, separators=(",", ":")) + "\n"
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(payload)
        except Exception:
            pass


if __name__ == "__main__":
    main()
