# src/app.py
from __future__ import annotations

import pandas as pd
import streamlit as st

from kpis import load_daily_fact, compute_kpis
from rules import classify_sites

st.set_page_config(page_title="Site Resource Ops Tool", layout="wide")


@st.cache_data
def load_and_compute(csv_path: str):
    df = load_daily_fact(csv_path)
    out = compute_kpis(df)
    status = classify_sites(out.by_site, out.by_site_day, out.loss_mix_by_site)
    return df, out, status


def main():
    st.title("Site Resource Utilization & Loss Prevention")
    st.caption("KPI computation + rules-based site classification (synthetic dataset)")

    csv_path = "data/raw/daily_site_resource.csv"
    df, kpi, status = load_and_compute(csv_path)

    # Sidebar filters
    st.sidebar.header("Filters")
    site_ids = sorted(df["site_id"].unique().tolist())
    selected_sites = st.sidebar.multiselect("Sites", site_ids, default=site_ids)

    df["date"] = pd.to_datetime(df["date"])
    date_min = df["date"].min().date()
    date_max = df["date"].max().date()
    start_date, end_date = st.sidebar.date_input("Date range", (date_min, date_max))

    dff = df[(df["site_id"].isin(selected_sites)) & (df["date"].dt.date >= start_date) & (df["date"].dt.date <= end_date)]

    # Recompute KPIs for filtered view
    kpi_f = compute_kpis(dff)
    status_f = classify_sites(kpi_f.by_site, kpi_f.by_site_day, kpi_f.loss_mix_by_site)

    # KPI tiles
    o = kpi_f.overall.iloc[0]
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Actual Units", f"{int(o['actual_units']):,}")
    c2.metric("Disposed Units", f"{int(o['disposed_units']):,}")
    c3.metric("Cost Leakage", f"${float(o['cost_leakage']):,.2f}")
    c4.metric("Avg Loss Rate", f"{float(o['avg_loss_rate'])*100:.2f}%")
    c5.metric("Avg Utilization", f"{float(o['avg_utilization_rate'])*100:.2f}%")

    st.divider()

    left, right = st.columns([1.35, 1.0])

    with left:
        st.subheader("Site Risk & Recommended Actions")
        st.dataframe(status_f, use_container_width=True, hide_index=True)

    with right:
        st.subheader("Top Sites by Cost Leakage")
        top = kpi_f.by_site.sort_values("cost_leakage", ascending=False).head(10)[["site_id", "cost_leakage"]]
        st.bar_chart(top.set_index("site_id"))

    st.divider()

    st.subheader("Trends (Filtered)")
    trend = (
        kpi_f.by_site_day.groupby("date", as_index=False)
        .agg(cost_leakage=("cost_leakage", "sum"), loss_rate=("loss_rate", "mean"))
        .sort_values("date")
    )
    t1, t2 = st.columns(2)
    with t1:
        st.caption("Cost Leakage ($/day)")
        st.line_chart(trend.set_index("date")["cost_leakage"])
    with t2:
        st.caption("Avg Loss Rate")
        st.line_chart(trend.set_index("date")["loss_rate"])

    st.divider()

    st.subheader("Loss Driver Mix (Filtered)")
    mix = (
        kpi_f.loss_mix_by_site.groupby("loss_reason", as_index=False)
        .agg(disposed_units=("disposed_units", "sum"))
        .sort_values("disposed_units", ascending=False)
    )
    st.bar_chart(mix.set_index("loss_reason")["disposed_units"])

    st.caption("Dashboard recomputes KPIs and status on the filtered subset.")


if __name__ == "__main__":
    main()
