import os

# WebSocket RPC（需替换为你的 Infura/Alchemy 密钥）
WS_RPC_URL = os.getenv("ETH_WS_URL", "wss://mainnet.infura.io/ws/v3/YOUR_PROJECT_ID")

# PAXG 合约地址（小写）
PAXG_ADDRESS = "0x45804880de22913dafe09f4980848ece6ecbaf78"

# Transfer 事件签名（keccak256("Transfer(address,address,uint256)"))
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

# 模型路径
MODEL_PATH = "models/factor_model_intent.pkl"

# 特征表路径（用于加载地址历史统计）
FEATURE_TABLE_PATH = "data/processed/paxg_transactions.parquet"

# 黄金价格更新间隔（秒）
GOLD_PRICE_UPDATE_INTERVAL = 60

# 信号推送阈值
MIN_TRADE_VALUE_USD = 1000.0   # 仅推送金额大于此值的交易