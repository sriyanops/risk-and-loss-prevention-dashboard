# src/main.py
from __future__ import annotations

from pathlib import Path

from kpis import load_daily_fact, compute_kpis
from rules import classify_sites


def main() -> None:
    root = Path(__file__).resolve().parents[1]

    data_path = root / "data" / "raw" / "daily_site_resource.csv"
    if not data_path.exists():
        raise FileNotFoundError(f"Missing data file: {data_path}")

    df = load_daily_fact(str(data_path))
    kpis = compute_kpis(df)
    site_status = classify_sites(
        kpis.by_site,
        kpis.by_site_day,
        kpis.loss_mix_by_site,
    )

    # Console summary (for now)
    print("\n=== OVERALL ===")
    print(kpis.overall.to_string(index=False))

    print("\n=== SITE STATUS (TOP RISK FIRST) ===")
    print(site_status.head(12).to_string(index=False))


if __name__ == "__main__":
    main()
