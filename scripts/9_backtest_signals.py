"""
回测验证脚本：检验意图信号对未来黄金价格变化的预测能力
输出：IC序列、分组收益、权益曲线、关键指标
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import spearmanr
import json
import os

# ===== 配置 =====
LABELED_DATA = "data/labeled/full_labeled.parquet"
GOLD_PRICE_DATA = "data/raw/gold_price.csv"
OUTPUT_DIR = "results/"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 预测窗口（小时）
FORECAST_HORIZONS = [1, 4, 24]

# 标签映射为数值信号
SIGNAL_MAP = {
    'accumulation': 1,
    'normal': 0,
    'distribution': -1
}

def load_data():
    """加载标注数据和黄金价格"""
    df = pd.read_parquet(LABELED_DATA)
    # 确保时间戳为datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    
    gold = pd.read_csv(GOLD_PRICE_DATA, parse_dates=['Date'])
    gold = gold.rename(columns={'Date': 'timestamp', 'Close': 'gold_price'})
    gold = gold.sort_values('timestamp')
    return df, gold

def calculate_future_returns(df, gold, horizon_hours):
    """计算每个交易发生后的未来黄金收益率"""
    # 将黄金价格对齐到交易时间戳
    gold['timestamp'] = pd.to_datetime(gold['timestamp'])
    df = pd.merge_asof(df, gold, on='timestamp', direction='backward')
    
    # 计算未来价格
    future_times = df['timestamp'] + pd.Timedelta(hours=horizon_hours)
    future_prices = []
    for t in future_times:
        idx = gold['timestamp'].searchsorted(t, side='right') - 1
        if idx >= 0:
            future_prices.append(gold.iloc[idx]['gold_price'])
        else:
            future_prices.append(np.nan)
    df[f'future_price_{horizon_h}h'] = future_prices
    df[f'return_{horizon_h}h'] = (df[f'future_price_{horizon_h}h'] - df['gold_price']) / df['gold_price']
    return df

def calculate_ic(df, horizon):
    """计算信号与未来收益的Spearman秩相关系数（IC）"""
    signal_col = 'signal'
    target_col = f'return_{horizon}h'
    valid = df[[signal_col, target_col]].dropna()
    if len(valid) < 10:
        return np.nan, np.nan
    ic, p_value = spearmanr(valid[signal_col], valid[target_col])
    return ic, p_value

def group_backtest(df, horizon, n_groups=5):
    """按信号分组回测：将信号分为5组，计算每组平均未来收益"""
    df = df.copy()
    # 按信号分位数分组
    df['group'] = pd.qcut(df['signal'], q=n_groups, labels=False, duplicates='drop')
    group_returns = df.groupby('group')[f'return_{horizon}h'].mean()
    return group_returns

def plot_equity_curve(df, horizon):
    """构建简单的多空组合权益曲线（信号>0做多，信号<0做空）"""
    df = df.copy()
    df['position'] = np.sign(df['signal'])  # 1,0,-1
    df['strategy_return'] = df['position'] * df[f'return_{horizon}h']
    df['cumulative_return'] = (1 + df['strategy_return']).cumprod()
    
    plt.figure(figsize=(10, 5))
    plt.plot(df['timestamp'], df['cumulative_return'], label=f'Strategy (horizon={horizon}h)')
    plt.title('Equity Curve of Signal-based Strategy')
    plt.xlabel('Time')
    plt.ylabel('Cumulative Return')
    plt.legend()
    plt.grid(True)
    plt.savefig(f'{OUTPUT_DIR}equity_curve_{horizon}h.png', dpi=150)
    plt.close()
    return df['cumulative_return'].iloc[-1] - 1  # 总收益

def main():
    print("加载数据...")
    df, gold = load_data()
    
    # 添加信号列
    df['signal'] = df['label_intent'].map(SIGNAL_MAP)
    print(f"数据集大小: {len(df)}")
    print(f"信号分布:\n{df['signal'].value_counts()}")
    
    results = {}
    for horizon in FORECAST_HORIZONS:
        print(f"\n===== 预测窗口: {horizon} 小时 =====")
        df_horizon = calculate_future_returns(df.copy(), gold, horizon)
        
        # 1. IC分析
        ic, p_value = calculate_ic(df_horizon, horizon)
        print(f"IC (Spearman): {ic:.4f}, p-value: {p_value:.4f}")
        
        # 2. 分组收益
        group_ret = group_backtest(df_horizon, horizon)
        print("分组平均收益:")
        print(group_ret)
        
        # 3. 权益曲线
        total_return = plot_equity_curve(df_horizon, horizon)
        print(f"多空策略总收益: {total_return*100:.2f}%")
        
        results[horizon] = {
            'ic': ic,
            'p_value': p_value,
            'group_returns': group_ret.to_dict(),
            'total_return': total_return
        }
    
    # 保存结果
    with open(f'{OUTPUT_DIR}backtest_metrics.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n回测结果已保存至 {OUTPUT_DIR}backtest_metrics.json")
    
    # 可选：绘制IC时间序列（按月滚动）
    # 此处略，可根据需要扩展

if __name__ == "__main__":
    main()