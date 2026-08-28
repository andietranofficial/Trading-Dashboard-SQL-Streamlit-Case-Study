"""Stock analysis trading dashboard for the ADM Capital Partners case study."""

from pathlib import Path

import altair as alt
import pandas as pd

import streamlit as st

DATA_DIR = Path(__file__).resolve().parent.parent / "Datasets"

VIEW_PERIODS = {"30D": 30, "90D": 90, "180D": 180, "1Y": 365, "All": None}
UP_COLOR = "#FB923C"
DOWN_COLOR = "#1D3557"
HIGHLIGHT_COLOR = "#60A5FA"
PEER_COLOR = "#94A3B8"

st.set_page_config(
    page_title="ADM Capital Partners Trading Dashboard",
    page_icon=":material/candlestick_chart:",
    layout="wide",
)


@st.cache_data(ttl="1h", show_spinner="Loading historical prices...")
def load_historical() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "HistoricalData.csv", parse_dates=["Date"])
    return df.sort_values("Date")


@st.cache_data(ttl="1h", show_spinner="Loading intraday attributes...")
def load_intraday() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "IntradayData.csv", parse_dates=["DateTime"])
    return df.sort_values("DateTime")


def filter_by_period(df: pd.DataFrame, date_col: str, period_label: str) -> pd.DataFrame:
    days = VIEW_PERIODS[period_label]
    if days is None or df.empty:
        return df
    cutoff = df[date_col].max() - pd.Timedelta(days=days)
    return df[df[date_col] >= cutoff]


@st.cache_data(ttl="1h")
def compute_period_returns(historical: pd.DataFrame, period_label: str) -> pd.DataFrame:
    """% change in AdjClose per ticker over the selected view period."""
    rows = []
    for symbol, group in historical.groupby("Symbol"):
        windowed = filter_by_period(group, "Date", period_label)
        if len(windowed) < 2:
            continue
        change = (windowed["AdjClose"].iloc[-1] / windowed["AdjClose"].iloc[0] - 1) * 100
        rows.append({"Symbol": symbol, "Change %": change})
    return pd.DataFrame(rows).sort_values("Change %", ascending=False).reset_index(drop=True)


def candlestick_chart(df: pd.DataFrame) -> alt.LayerChart:
    df = df.copy()
    df["Direction"] = (df["Close"] >= df["Open"]).map({True: "Up", False: "Down"})
    color = alt.Color(
        "Direction:N",
        scale=alt.Scale(domain=["Up", "Down"], range=[UP_COLOR, DOWN_COLOR]),
        legend=None,
    )

    base = alt.Chart(df).encode(x=alt.X("Date:T", title=None), color=color)
    return (
        base.mark_rule().encode(y=alt.Y("Low:Q", title="Price (USD)").scale(zero=False), y2="High:Q")
        + base.mark_bar(size=4).encode(y="Open:Q", y2="Close:Q")
    ).properties(height=260, width="container")


def volume_chart(df: pd.DataFrame) -> alt.Chart:
    df = df.copy()
    df["Direction"] = (df["Close"] >= df["Open"]).map({True: "Up", False: "Down"})
    color = alt.Color(
        "Direction:N",
        scale=alt.Scale(domain=["Up", "Down"], range=[UP_COLOR, DOWN_COLOR]),
        legend=None,
    )
    return (
        alt.Chart(df)
        .mark_bar()
        .encode(x=alt.X("Date:T", title=None), y=alt.Y("Volume:Q", title="Volume"), color=color)
        .properties(height=260, width="container")
    )


def bollinger_chart(df: pd.DataFrame, window: int, num_std: float) -> alt.LayerChart:
    df = df.copy().sort_values("Date")
    df["MA"] = df["Close"].rolling(window).mean()
    std = df["Close"].rolling(window).std()
    df["Upper"] = df["MA"] + num_std * std
    df["Lower"] = df["MA"] - num_std * std

    base = alt.Chart(df).encode(x=alt.X("Date:T", title=None))
    band = base.mark_area(opacity=0.15, color=HIGHLIGHT_COLOR).encode(
        y=alt.Y("Lower:Q", title="Price (USD)").scale(zero=False), y2="Upper:Q"
    )
    moving_average = base.mark_line(color=HIGHLIGHT_COLOR).encode(y="MA:Q")
    close_price = base.mark_line(color=UP_COLOR).encode(y="Close:Q")
    return (band + moving_average + close_price).properties(height=280, width="container")


def relative_change_chart(historical_window: pd.DataFrame, symbol: str) -> alt.LayerChart:
    pivot = historical_window.pivot(index="Date", columns="Symbol", values="AdjClose")
    normalized = (pivot.div(pivot.bfill().iloc[0]) - 1) * 100
    long_df = normalized.reset_index().melt(id_vars="Date", var_name="Symbol", value_name="Change %")

    base = alt.Chart(long_df)
    peers = (
        base.transform_filter(alt.datum.Symbol != symbol)
        .mark_line(opacity=0.35, color=PEER_COLOR)
        .encode(x=alt.X("Date:T", title=None), y=alt.Y("Change %:Q").scale(zero=False), detail="Symbol:N")
    )
    highlighted = (
        base.transform_filter(alt.datum.Symbol == symbol)
        .mark_line(color=HIGHLIGHT_COLOR, size=2.5)
        .encode(x=alt.X("Date:T", title=None), y=alt.Y("Change %:Q").scale(zero=False))
    )
    return (peers + highlighted).properties(height=280, width="container")


historical = load_historical()
intraday = load_intraday()
all_symbols = sorted(historical["Symbol"].unique())

if "selected_symbol" not in st.session_state:
    st.session_state.selected_symbol = all_symbols[0]

with st.sidebar:
    view_period = st.segmented_control(
        "View period", list(VIEW_PERIODS), default="180D", label_visibility="visible"
    )
    if view_period is None:
        view_period = "180D"

    selectbox_symbol = st.selectbox(
        "Ticker selection", all_symbols, index=all_symbols.index(st.session_state.selected_symbol)
    )
    if selectbox_symbol != st.session_state.selected_symbol:
        st.session_state.selected_symbol = selectbox_symbol
        st.rerun()

    st.markdown(f"**Dow 30 performance ({view_period})**")
    returns = compute_period_returns(historical, view_period)
    styled = returns.style.background_gradient(subset=["Change %"], cmap="coolwarm")
    event = st.dataframe(
        styled,
        column_config={"Change %": st.column_config.NumberColumn(format="%.2f%%")},
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        height=600,
    )
    if event.selection.rows:
        clicked_symbol = returns.iloc[event.selection.rows[0]]["Symbol"]
        if clicked_symbol != st.session_state.selected_symbol:
            st.session_state.selected_symbol = clicked_symbol
            st.rerun()

symbol = st.session_state.selected_symbol
sec_hist_all = historical[historical["Symbol"] == symbol]
sec_hist = filter_by_period(sec_hist_all, "Date", view_period)
sec_intra = intraday[intraday["Symbol"] == symbol]
company = sec_hist_all["Company"].iloc[0]
exchange = sec_hist_all["Exchange"].iloc[0]
latest_day = sec_hist_all.iloc[-1]
latest_tick = sec_intra.iloc[-1] if not sec_intra.empty else None

st.title(":material/candlestick_chart: ADM Capital Partners Trading Dashboard", text_alignment="center")
st.caption(
    f"latest trading day: {latest_day['Date'].date()}  · author: Andie Tran",
    text_alignment="center",
)

info_col, kpi_col = st.columns([1, 5], vertical_alignment="center")
with info_col:
    st.caption(exchange)
    st.header(symbol)
    st.caption(company)

with kpi_col:
    with st.container(horizontal=True):
        if latest_tick is not None:
            st.metric("Beta (5Y monthly)", f"{latest_tick['Beta']:.2f}", border=True)
            st.metric("Latest bid", f"${latest_tick['LastBid']:.2f}", border=True)
            st.metric("Market cap (MM)", f"{latest_tick['MarketCap'] / 1e6:,.0f}M", border=True)
        st.metric("Latest day's high", f"${latest_day['High']:.2f}", border=True)
        st.metric("Latest day's low", f"${latest_day['Low']:.2f}", border=True)
        st.metric("Latest day's open", f"${latest_day['Open']:.2f}", border=True)
        st.metric("Volume", f"{latest_day['Volume']:,.0f}", border=True)

with st.container(border=True):
    st.markdown(f"**{view_period} daily volume and price movements** — {exchange}:{symbol}")
    st.altair_chart(candlestick_chart(sec_hist), width="stretch")
    st.altair_chart(volume_chart(sec_hist), width="stretch")

col1, col2 = st.columns(2)
with col1:
    with st.container(border=True, height="stretch"):
        st.markdown(f"**{view_period} Bollinger chart** — {exchange}:{symbol}")
        settings = st.columns(2)
        lookback = settings[0].number_input("Lookback period (MA)", min_value=2, max_value=100, value=20)
        num_std = settings[1].number_input("# of STDEV", min_value=1.0, max_value=4.0, value=2.0, step=0.5)
        st.altair_chart(bollinger_chart(sec_hist, lookback, num_std), width="stretch")

with col2:
    with st.container(border=True, height="stretch"):
        st.markdown(f"**{view_period} relative price change** — {symbol} vs Dow 30")
        window_all = filter_by_period(historical, "Date", view_period)
        st.altair_chart(relative_change_chart(window_all, symbol), width="stretch")
