import pandas_datareader as pdr
import pandas as pd
from datetime import datetime

try:
    # 从 Stooq 获取 GLD 数据
    df = pdr.DataReader('GLD', 'stooq', start='2024-01-01')
    # 重置索引，使日期成为列
    df = df.reset_index()
    # 只保留日期和收盘价，重命名
    df = df[['Date', 'Close']].rename(columns={'Close': 'gold_price'})
    # 保存为CSV
    df.to_csv('data/raw/gold_price.csv', index=False)
    print(f"成功获取 {len(df)} 条黄金价格数据，保存至 data/raw/gold_price.csv")
except Exception as e:
    print(f"获取失败: {e}")
    print("请尝试手动下载：访问 https://stooq.com/q/d/?s=gld.us 并导出数据")