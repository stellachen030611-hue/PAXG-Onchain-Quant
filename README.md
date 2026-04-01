# PAXG Onchain Quant – On-Chain Gold Token Quant Factor & AI Strategy

![Python](https://img.shields.io/badge/Python-3.10-blue)
![Web3](https://img.shields.io/badge/Web3.py-6.0+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

Automatically fetch PAXG transfer events, use LLM initial labeling + manual review to build a training dataset, train a Random Forest model to predict transaction intent (accumulation/distribution/normal), and implement real-time prediction, backtesting validation, and a Streamlit dashboard.

## System Architecture

```mermaid
graph TD
    A[Ethereum Mainnet] -->|Web3.py Polling/WebSocket| B(PAXG Transfer Event)
    B --> C{Data Pipeline}
    C --> D[Raw Data Storage<br>data/raw/]
    D --> E[Feature Engineering<br>3_preprocess_features.py]
    E --> F[Feature Table<br>data/processed/]
    G[Gold Price API<br>yfinance/Stooq] --> E
    F --> H[Auto Labeling<br>7_auto_label.py + Ollama]
    H --> I[Labeled Dataset<br>data/labeled/]
    I --> J[Model Training<br>8_factor_mining.py]
    J --> K[Random Forest Model<br>models/factor_model_intent.pkl]
    K --> L[Real-time Prediction Module<br>realtime/run_realtime.py]
    L --> M[Real-time Predictions<br>realtime/predictions.jsonl]
    M --> N[Streamlit Dashboard<br>app.py]
    K --> O[Backtesting Module<br>backtest/run_backtest.py]
    O --> P[Equity Curve / Drawdown / Sharpe Ratio<br>results/backtest/]


```markdown

## Key Features

- On-chain data collection (Web3.py)
- Feature engineering (balance, amount, time, gold price changes)
- Auto labeling (Ollama + Gemma3)
- Model training (Random Forest, output feature importance)
- Real-time prediction (WebSocket listening, real-time decisions)
- Backtesting engine (simulated trading, Sharpe ratio, etc.)
- Visualization dashboard (Streamlit)
- Quick start: environment setup, dependency installation, data acquisition, pipeline execution
- Example results: feature importance chart, backtest equity curve, real-time prediction screenshots
- Project structure: brief directory tree description

## Tech Stack

Python, Web3, Pandas, Scikit-learn, Streamlit, Ollama, etc.

## Project Directory Tree

```
PAXG-Onchain-Quant/
├── data/                     # Data storage
│   ├── raw/                  # Raw on-chain events, gold price CSV
│   ├── processed/            # Feature table (Parquet), labeling checkpoint files
│   ├── labeled/              # Split train/val/test datasets
│   ├── realtime/             # Real-time prediction records (generated on the fly)
│   └── sample/               # Minimal sample data
├── scripts/                  # Data processing pipeline (execute in order)
│   ├── 1_fetch_paxg_transfers.py
│   ├── 2_fetch_gold_price.py
│   ├── 3_preprocess_features.py
│   ├── 6_build_dataset.py
│   ├── 7_auto_label.py
│   └── 8_factor_mining.py
├── realtime/                 # Real-time prediction module
│   ├── config.py             # RPC, model path, threshold config
│   ├── state_cache.py        # Address balance, gold price cache
│   ├── feature_extractor.py  # Real-time feature computation
│   ├── predictor.py          # Load model, predict intent
│   ├── stream_handler.py     # Save prediction results to file
│   └── run_realtime.py       # Main entry: listen to new blocks and predict
├── backtest/                 # Backtesting module (strategy validation)
│   ├── config.py             # Backtest parameters (capital, fee, thresholds)
│   ├── signals.py            # Generate buy/sell signals based on predictions
│   ├── engine.py             # Simulation trading engine
│   ├── metrics.py            # Sharpe ratio, max drawdown, etc.
│   └── run_backtest.py       # Execute backtest and output results
├── models/                   # Trained models
│   └── factor_model_intent.pkl
├── results/backtest/         # Backtest outputs (images, metrics, trade details)
├── app.py                    # Streamlit visualization dashboard
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (ETH_RPC_URL, etc.)
└── README.md
```

## Complete Data Generation Guide

### 1. Create and activate environment
```bash
conda create -n web3-gold python=3.10
conda activate web3-gold
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Create `.env` file and fill in your Ethereum node URL (e.g., Infura/Alchemy)
```bash
echo ETH_RPC_URL=https://mainnet.infura.io/v3/YOUR_PROJECT_ID > .env
```

### 4. Configure Ollama local model
```bash
ollama pull gemma3:4b
```

### 5. Data collection & feature engineering
```bash
python scripts/1_fetch_paxg_transfers.py      # Fetch PAXG transfers from Ethereum (~26k events)
python scripts/2_fetch_gold_price.py          # Download gold price data (manual download if auto fails)
python scripts/3_preprocess_features.py       # Feature engineering, generate feature table
```

### 6. AI auto labeling (optional, or use existing labels)
- Modify `SAMPLE_SIZE` in `scripts/7_auto_label.py` to your desired number (e.g., 500; set to 10 for testing)
```bash
python scripts/7_auto_label.py                # Call Ollama for labeling (may take hours)
```

### 7. Build dataset & train model
```bash
python scripts/6_build_dataset.py             # Merge labels with features
python scripts/8_factor_mining.py             # Train Random Forest, output feature importance
```

### 8. Backtesting (optional)
```bash
python backtest/run_backtest.py
```

### 9. Real-time monitoring (optional)
```bash
python realtime/run_realtime.py
```

### 10. Launch dashboard (will use the full dataset)
```bash
streamlit run app.py
```

## Quick Start Guide

1. Clone the repository and install dependencies.
2. Run `streamlit run app.py` to see the pre-built dashboard.

> Sample data is located at `data/sample/sample_labeled.parquet`; no need to run the full data generation process.
```