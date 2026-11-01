# 📈 Algorithmic Trading Backtester

A quantitative finance tool that backtests a **Moving Average Crossover Strategy** on any stock using real historical data.

## 🚀 Live Demo
> Deploy on [Streamlit Cloud](https://streamlit.io/cloud) — free in 2 minutes

## 📊 Features
- Moving Average Crossover strategy (configurable short/long SMA)
- Real-time stock data via Yahoo Finance API
- Key risk metrics: **Sharpe Ratio**, **Max Drawdown**, **Total Return**
- Buy/Sell signal visualization on price chart
- Portfolio value tracking vs Buy & Hold benchmark
- Full trade log

## 🛠️ Tech Stack
- **Python** — Core logic
- **yfinance** — Real market data
- **Pandas / NumPy** — Data processing & metrics
- **Matplotlib** — Charting
- **Streamlit** — Interactive dashboard

## ⚙️ How to Run Locally

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/trading-backtester
cd trading-backtester

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
streamlit run backtester.py
```

## 📐 Strategy Logic

```
BUY  signal → when Short SMA crosses ABOVE Long SMA
SELL signal → when Short SMA crosses BELOW Long SMA
```

## 📈 Metrics Explained
| Metric | What it means |
|--------|--------------|
| Sharpe Ratio | Return per unit of risk (higher = better) |
| Max Drawdown | Worst peak-to-trough loss |
| Total Return | Overall % gain/loss |

## 🔧 Possible Improvements
- Add RSI / Bollinger Bands strategies
- Add transaction cost modeling
- Add position sizing (Kelly Criterion)
- Add multi-stock portfolio backtesting

## 📁 Project Structure
```
trading-backtester/
├── backtester.py      # Main app
├── requirements.txt   # Dependencies
└── README.md          # This file
```
