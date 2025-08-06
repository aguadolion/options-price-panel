"""
Streamlit application for viewing option price data from Polygon.io.

This MVP fetches option contract metadata for a given underlying ticker and
shows the previous day's OHLC (open, high, low, close) values for each option.

The API key for Polygon should be supplied via an environment variable
``POLYGON_API_KEY`` or through Streamlit's secrets configuration as
``polygon_api_key``. Without a valid key, the app will alert the user.
"""

import os
from typing import List, Tuple, Optional, Dict

import streamlit as st
import pandas as pd
import requests


def get_api_key() -> str:
    """Retrieve the Polygon API key from environment variables or Streamlit secrets.

    Returns
    -------
    str
        The API key if found, otherwise an empty string.
    """
    # First check environment variable
    api_key = os.getenv("POLYGON_API_KEY")
    if api_key:
        return api_key
    # Fallback to Streamlit secrets if configured
    if st.secrets and "polygon_api_key" in st.secrets:
        return st.secrets["polygon_api_key"]
    return ""


def fetch_contracts(underlying: str, limit: int, api_key: str) -> Tuple[List[Dict], Optional[str]]:
    """Fetch option contract metadata for a given underlying ticker.

    Parameters
    ----------
    underlying : str
        The stock ticker symbol for the underlying asset (e.g., 'AAPL').
    limit : int
        Number of contracts to fetch.
    api_key : str
        The Polygon API key.

    Returns
    -------
    Tuple[List[Dict], Optional[str]]
        A tuple containing a list of contract dictionaries and an optional
        error message. If an error occurs, the list will be empty and
        the error message will contain details.
    """
    url = "https://api.polygon.io/v3/reference/options/contracts"
    params = {
        "underlying_ticker": underlying.upper(),
        "limit": limit,
        "apiKey": api_key,
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
    except requests.RequestException as e:
        return [], f"Request error: {e}"
    if resp.status_code != 200:
        try:
            message = resp.json().get("message", f"HTTP {resp.status_code}")
        except Exception:
            message = f"HTTP {resp.status_code}"
        return [], f"Failed to fetch contracts: {message}"
    data = resp.json().get("results", [])
    return data, None


def fetch_prev_agg(option_ticker: str, api_key: str) -> Optional[Dict]:
    """Fetch previous day aggregate (OHLC) data for a specific option ticker.

    Parameters
    ----------
    option_ticker : str
        The full option ticker (e.g., 'O:AAPL240816C00180000').
    api_key : str
        The Polygon API key.

    Returns
    -------
    Optional[Dict]
        A dictionary containing OHLC data if available, else None.
    """
    url = f"https://api.polygon.io/v2/aggs/ticker/{option_ticker}/prev"
    params = {"apiKey": api_key}
    try:
        resp = requests.get(url, params=params, timeout=10)
    except requests.RequestException:
        return None
    if resp.status_code != 200:
        return None
    results = resp.json().get("results", [])
    return results[0] if results else None


def fetch_last_trade(option_ticker: str, api_key: str) -> Optional[float]:
    """Fetch the most recent trade price for a specific option ticker.

    The Polygon trades endpoint returns individual trades for an instrument. This
    helper retrieves the latest trade (if any) and extracts the price. If
    trading is halted or the market is closed, the endpoint may return no
    results, in which case ``None`` is returned.

    Parameters
    ----------
    option_ticker : str
        The full option ticker (e.g., ``O:AAPL240816C00180000``).
    api_key : str
        The Polygon API key.

    Returns
    -------
    Optional[float]
        The latest traded price if available, otherwise ``None``.
    """
    url = f"https://api.polygon.io/v3/trades/{option_ticker}"
    params = {
        "limit": 1,
        "apiKey": api_key,
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
    except requests.RequestException:
        return None
    if resp.status_code != 200:
        return None
    data = resp.json().get("results", [])
    if not data:
        return None
    trade = data[0]
    # Trades responses may use "p" (price) or "price" depending on the API version
    price = trade.get("p") or trade.get("price")
    return float(price) if price is not None else None


def build_dataframe(contracts: List[Dict], api_key: str) -> pd.DataFrame:
    """Construct a pandas DataFrame combining contract metadata with price data.

    This function enriches each option contract with both the most recent trade
    price (if available) and the previous day's OHLC values. The returned
    DataFrame includes numeric premium values for filtering and a source flag
    indicating whether the premium comes from real‑time data or the previous
    close.

    Parameters
    ----------
    contracts : List[Dict]
        A list of contract metadata dictionaries.
    api_key : str
        The Polygon API key.

    Returns
    -------
    pd.DataFrame
        A DataFrame with columns for ticker, contract type, strike price,
        expiration date, previous day's OHLC values, a numeric premium and
        a premium source indicator.
    """
    rows = []
    for contract in contracts:
        ticker = contract.get("ticker")
        # Fetch previous day's aggregated data
        prev = fetch_prev_agg(ticker, api_key)
        # Fetch the latest trade price; may return None if no trade is available
        last_price = fetch_last_trade(ticker, api_key)
        # Determine the premium: use real‑time price if available, otherwise fall back to previous close
        close_price = prev.get("c") if prev else None
        if last_price is not None:
            premium_value = last_price
            premium_source = "real"
        else:
            premium_value = close_price
            premium_source = "close"
        row = {
            "Option Ticker": ticker,
            "Type": contract.get("contract_type"),
            "Strike": contract.get("strike_price"),
            "Expiration": contract.get("expiration_date"),
            "Close": close_price,
            "Open": prev.get("o") if prev else None,
            "High": prev.get("h") if prev else None,
            "Low": prev.get("l") if prev else None,
            "Premium": premium_value,
            "PremiumSource": premium_source,
        }
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    """Run the Streamlit app."""
    st.title("Options Price Panel (MVP)")
    st.markdown(
        """
        Enter a stock ticker to retrieve option contracts and view the previous day's
        open, high, low and close prices for each contract. This is an MVP
        demonstrating basic connectivity to Polygon.io's REST API. To use
        this app, provide a valid Polygon API key via an environment variable
        named `POLYGON_API_KEY` or add it to your Streamlit secrets as
        `polygon_api_key`.
        """,
        help="Provide your Polygon API key via environment variable or Streamlit secrets.",
    )
    api_key = get_api_key()
    ticker_input = st.text_input(
        "Underlying ticker (e.g., AAPL)",
        value="AAPL",
    )
    limit = st.number_input(
        "Number of options to display",
        min_value=1,
        max_value=50,
        value=5,
        step=1,
    )
    if st.button("Fetch option prices"):
        if not api_key:
            st.error(
                "API key is missing. Set POLYGON_API_KEY env var or configure Streamlit secrets."
            )
        else:
            with st.spinner("Fetching data..."):
                contracts, error = fetch_contracts(ticker_input, int(limit), api_key)
            if error:
                st.error(error)
            elif not contracts:
                st.warning("No contracts found for the specified underlying ticker.")
            else:
                df = build_dataframe(contracts, api_key)
                # Normalize option types to lowercase for filtering
                df["Type"] = df["Type"].str.lower()
                # Allow the user to filter option types (call or put)
                option_types = st.multiselect(
                    "Filter by option type",
                    options=["call", "put"],
                    default=["call", "put"],
                )
                df_filtered = df[df["Type"].isin(option_types)].copy()
                # Determine the range for the premium slider using the numeric Premium column
                valid_premiums = df_filtered["Premium"].dropna()
                if not valid_premiums.empty:
                    min_price = float(valid_premiums.min())
                    max_price = float(valid_premiums.max())
                else:
                    min_price = 0.0
                    max_price = 0.0
                price_min, price_max = st.slider(
                    "Filter by premium",
                    min_value=min_price,
                    max_value=max_price,
                    value=(min_price, max_price),
                )
                # Apply the selected premium range filters
                df_filtered = df_filtered[
                    (df_filtered["Premium"].fillna(0) >= price_min) &
                    (df_filtered["Premium"].fillna(0) <= price_max)
                ].copy()
                # Build a display-friendly Premium string with ' C' suffix if using previous close
                def format_premium(value: Optional[float], source: str) -> Optional[str]:
                    if value is None:
                        return None
                    return f"{value} C" if source == "close" else f"{value}"

                df_filtered["PremiumDisplay"] = df_filtered.apply(
                    lambda row: format_premium(row["Premium"], row["PremiumSource"]),
                    axis=1,
                )
                # Display the filtered data with relevant columns
                display_cols = [
                    "Option Ticker",
                    "Type",
                    "Strike",
                    "Expiration",
                    "PremiumDisplay",
                    "PremiumSource",
                    "Open",
                    "High",
                    "Low",
                ]
                st.dataframe(
                    df_filtered[display_cols].rename(columns={"PremiumDisplay": "Premium"}),
                    use_container_width=True,
                )


if __name__ == "__main__":
    main()
