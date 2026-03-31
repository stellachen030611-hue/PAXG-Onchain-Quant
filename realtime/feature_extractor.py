import pandas as pd
import numpy as np
from datetime import datetime
import requests
import yfinance as yf

def get_current_gold_price():
    """获取当前黄金价格（美元/盎司）"""
    try:
        gld = yf.Ticker("GLD")
        data = gld.history(period="1d")
        if not data.empty:
            return data['Close'].iloc[-1]
    except Exception:
        pass
    # 备用：从网页抓取或使用缓存
    return 400.0  # 默认值

def compute_features(tx_data, state_cache, gold_price):
    """
    输入：
        tx_data: dict 包含 from_addr, to_addr, value（PAXG数量）, timestamp
        state_cache: 状态缓存对象
        gold_price: 当前黄金价格
    输出：
        features: dict 与模型训练时相同的特征
    """
    from_addr = tx_data['from_addr']
    to_addr = tx_data['to_addr']
    amount = tx_data['value']          # PAXG
    timestamp = tx_data['timestamp']   # datetime 对象

    # 获取地址历史余额（累计流入/流出）
    from_total_out = state_cache.get_balance_prior(from_addr, is_sender=True)
    to_total_in = state_cache.get_balance_prior(to_addr, is_sender=False)

    # 本次交易后的余额（用于特征“交易前余额”）
    from_balance_prior = from_total_out
    to_balance_prior = to_total_in

    # 金额美元价值
    value_usd = amount * gold_price

    # 时间特征
    hour = timestamp.hour
    day_of_week = timestamp.weekday()

    # 黄金价格变化（需要过去1小时价格，这里简化，使用全局缓存的过去1小时价格）
    # 实际上需要维护历史黄金价格序列，这里用当前价格（需改进）
    gold_price_change_1h = 0.0  # 简化，后续可增强

    # 组装特征（必须与训练时的列名完全一致）
    features = {
        'value': amount,
        'value_usd': value_usd,
        'from_balance_prior': from_balance_prior,
        'to_balance_prior': to_balance_prior,
        'hour': hour,
        'day_of_week': day_of_week,
        'gold_price_at_tx': gold_price,
        'gold_price_change_1h': gold_price_change_1h,
        # 如果有其他特征，如 from_total_out 等，也需加入
        'from_total_out': from_total_out,
        'to_total_in': to_total_in,
    }
    return features

def get_feature_dataframe(features_dict):
    """将特征字典转为 DataFrame，用于模型预测"""
    df = pd.DataFrame([features_dict])
    # 确保所有需要的列都存在，缺失的补默认值（与训练时填充策略一致）
    required_cols = [
        'value', 'value_usd', 'from_balance_prior', 'to_balance_prior',
        'hour', 'day_of_week', 'gold_price_at_tx', 'gold_price_change_1h',
        'from_total_out', 'to_total_in'
    ]
    for col in required_cols:
        if col not in df.columns:
            df[col] = 0.0
    return df