import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()
w3 = Web3(Web3.HTTPProvider(os.getenv("ETH_RPC_URL")))

def normalize_hash(hash_val):
    """将任意格式哈希转为无0x小写十六进制字符串"""
    if isinstance(hash_val, bytes):
        return hash_val.hex()
    s = str(hash_val).strip()
    if s.startswith('0x'):
        s = s[2:]
    return s.lower()

# 加载原始事件
with open("data/raw/paxg_transfers.json", "r") as f:
    events = json.load(f)

if not events:
    raise Exception("没有事件数据")

# 获取唯一区块号并估算时间
block_numbers = sorted(set(ev['blockNumber'] for ev in events))
print(f"共有 {len(block_numbers)} 个唯一区块")

# 估算时间范围（如果RPC失败则用默认）
try:
    first_block = w3.eth.get_block(block_numbers[0])
    last_block = w3.eth.get_block(block_numbers[-1])
    first_time = datetime.fromtimestamp(first_block['timestamp'])
    last_time = datetime.fromtimestamp(last_block['timestamp'])
    print(f"区块范围: {block_numbers[0]} ({first_time}) -> {block_numbers[-1]} ({last_time})")
except:
    first_time = datetime.now() - timedelta(days=1)
    last_time = datetime.now()
    print(f"使用估算时间: {first_time} -> {last_time}")

def get_timestamp(block_num):
    ratio = (block_num - block_numbers[0]) / (block_numbers[-1] - block_numbers[0])
    return first_time + (last_time - first_time) * ratio

# 构建DataFrame
rows = []
for ev in events:
    args = ev['args']
    tx_hash_raw = ev['transactionHash']          # 已是标准化十六进制
    tx_hash_hex = normalize_hash(tx_hash_raw)    # 确保一致
    rows.append({
        'blockNumber': ev['blockNumber'],
        'transactionHash': tx_hash_raw,
        'transactionHash_hex': tx_hash_hex,
        'logIndex': ev['logIndex'],
        'from_addr': args['from'],
        'to_addr': args['to'],
        'value': int(args['value']) / 1e18,
        'timestamp': get_timestamp(ev['blockNumber'])
    })
df = pd.DataFrame(rows)
df = df.sort_values('timestamp').reset_index(drop=True)
df['timestamp'] = pd.to_datetime(df['timestamp'])

# 加载黄金价格
gold_file = "data/raw/gold_price.csv"
if not os.path.exists(gold_file):
    raise FileNotFoundError("黄金价格文件不存在")
gold_df = pd.read_csv(gold_file)
if 'Date' in gold_df.columns:
    gold_df.rename(columns={'Date': 'date'}, inplace=True)
gold_df['date'] = pd.to_datetime(gold_df['date'])
gold_df = gold_df[['date', 'gold_price']].dropna().sort_values('date')
gold_df = gold_df.set_index('date').resample('1min').ffill().reset_index()
print(f"黄金价格数据已加载，共 {len(gold_df)} 条分钟数据")

# 匹配价格
df_sorted = df.sort_values('timestamp').reset_index(drop=True)
gold_sorted = gold_df.sort_values('date')
merged = pd.merge_asof(df_sorted, gold_sorted, left_on='timestamp', right_on='date', direction='backward')
df['gold_price_at_tx'] = merged['gold_price']

# 地址累计余额
from_balance = df.groupby('from_addr')['value'].sum().reset_index(name='from_total_out')
to_balance = df.groupby('to_addr')['value'].sum().reset_index(name='to_total_in')
df = df.merge(from_balance, on='from_addr', how='left')
df = df.merge(to_balance, on='to_addr', how='left')
df['from_balance_prior'] = df['from_total_out'] - df['value']
df['to_balance_prior'] = df['to_total_in'] - df['value']

# 简单特征
df['hour'] = df['timestamp'].dt.hour
df['day_of_week'] = df['timestamp'].dt.dayofweek
df['value_usd'] = df['value'] * df['gold_price_at_tx']

# 黄金价格变化：过去1小时的价格变化
df_1h = df[['timestamp']].copy()
df_1h['timestamp_1h'] = df_1h['timestamp'] - pd.Timedelta(hours=1)
merged_1h = pd.merge_asof(df_1h.sort_values('timestamp_1h'), gold_sorted, left_on='timestamp_1h', right_on='date', direction='backward')
df['gold_price_1h_ago'] = merged_1h['gold_price']
df['gold_price_change_1h'] = (df['gold_price_at_tx'] - df['gold_price_1h_ago']) / df['gold_price_1h_ago'] * 100

# 保存
os.makedirs("data/processed", exist_ok=True)
df.to_parquet("data/processed/paxg_transactions.parquet", index=False)
print(f"特征宽表已保存，共 {len(df)} 行，{len(df.columns)} 列")