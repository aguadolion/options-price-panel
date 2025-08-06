# Options Price Panel (MVP)

This repository contains a simple Streamlit application that connects to
[Polygon.io](https://polygon.io/) to retrieve option contract data for a given
underlying stock ticker and display the previous day's price information for
those contracts. The goal is to provide a minimal viable product (MVP) for
exploring option prices, with a foundation that can be improved and extended
over time.

## Features

- **User input for underlying ticker** – enter a stock symbol such as `AAPL`.
- **Control the number of contracts** – choose how many option contracts to
  retrieve and display (1–50).
- **Contract metadata** – view each option's strike price, contract type
  (call/put), and expiration date.
- **Previous day OHLC** – see the previous trading day's open, high, low and
  closing price for each option contract.

## Getting Started

### Prerequisites

* Python\u00a03.10 or higher
* A Polygon.io API key with access to option data. You can sign up at
  [polygon.io](https://polygon.io/). Some endpoints (such as real‑time
  snapshots) require higher‑tier subscriptions, but the endpoints used in
  this MVP (reference and previous aggregate data) are available on the
  free tier.

### Installation

Clone this repository and install the dependencies:

```bash
git clone https://github.com/yourusername/options-price-panel.git
cd options-price-panel
pip install -r requirements.txt
```

### Configuration

The application needs a Polygon API key to function. There are two ways to
provide the key:

1. **Environment variable** – set `POLYGON_API_KEY` in your shell or
   environment before running the app:

   ```bash
   export POLYGON_API_KEY=your_api_key_here
   streamlit run streamlit_app.py
   ```

2. **Streamlit secrets** – create a `.streamlit/secrets.toml` file with the
   following content:

   ```toml
   polygon_api_key = "your_api_key_here"
   ```

   Then run the app normally:

   ```bash
   streamlit run streamlit_app.py
   ```

Do **not** commit your API key to version control or share it publicly.

### Usage

Once configured, start the Streamlit server:

```bash
streamlit run streamlit_app.py
```

The application will open in your browser. Enter an underlying ticker and
specify how many option contracts you'd like to view. Click **Fetch option
prices** to retrieve the contracts and display their price information in a
table.

## Future Work

This MVP provides a foundation for interacting with Polygon's options data.
Potential enhancements include:

- Real‑time price updates and interactive charts.
- Filtering contracts by expiration date, strike range, or option type.
- Displaying additional metrics such as implied volatility, greeks or open
  interest (depending on API entitlements).
- Incorporating caching to reduce API calls and improve responsiveness.

Contributions and suggestions are welcome!
