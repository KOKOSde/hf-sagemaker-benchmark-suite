from __future__ import annotations

import argparse
import json


def monthly_cost(hourly_usd: float, hours_per_month: float = 730.0) -> float:
    return hourly_usd * hours_per_month


def main() -> None:
    p = argparse.ArgumentParser(description="Estimate monthly cost from hourly USD rate.")
    p.add_argument("--hourly-usd", type=float, required=True)
    p.add_argument("--hours-per-month", type=float, default=730.0)
    args = p.parse_args()
    out = {
        "hourly_usd": args.hourly_usd,
        "hours_per_month": args.hours_per_month,
        "monthly_usd": monthly_cost(args.hourly_usd, args.hours_per_month),
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()

