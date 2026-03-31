import sys
import os
# 将项目根目录加入模块搜索路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import joblib
import json
import matplotlib.pyplot as plt
from backtest import config, signals, engine, metrics

def main():
    # 1. 加载特征数据
    df = pd.read_parquet("data/processed/paxg_transactions.parquet")
    
    # 确保有标准化哈希列
    if 'transactionHash_hex' not in df.columns:
        def normalize_hash(h):
            if isinstance(h, bytes):
                return h.hex()
            s = str(h).lower().replace('0x', '')
            return s
        df['transactionHash_hex'] = df['transactionHash'].apply(normalize_hash)
    
    # 2. 加载模型
    model = joblib.load("models/factor_model_intent.pkl")
    
    # 3. 生成信号
    df_signals = signals.generate_signals(df, model, config)
    
    # 4. 运行回测
    equity_df, trades_df, final_capital = engine.run_backtest(df_signals, config)
    
    # 5. 计算绩效
    metrics_dict = metrics.calculate_metrics(equity_df['equity'], config.INITIAL_CAPITAL)
    metrics_dict['final_capital'] = final_capital
    
    # 6. 保存结果
    os.makedirs("results/backtest", exist_ok=True)
    with open("results/backtest/metrics.json", "w") as f:
        json.dump(metrics_dict, f, indent=2, default=str)
    trades_df.to_csv("results/backtest/trades.csv", index=False)
    
    # 7. 绘制权益曲线
    plt.figure(figsize=(12, 6))
    plt.plot(equity_df.index, equity_df['equity'], label='Equity Curve')
    plt.title('Backtest Equity Curve')
    plt.xlabel('Date')
    plt.ylabel('Equity (USDT)')
    plt.legend()
    plt.grid(True)
    plt.savefig("results/backtest/equity_curve.png")
    plt.show()
    
    # 8. 绘制回撤曲线
    returns = equity_df['equity'].pct_change().dropna()
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    plt.figure(figsize=(12, 4))
    plt.plot(drawdown.index, drawdown * 100, color='red')
    plt.title('Drawdown Curve')
    plt.xlabel('Date')
    plt.ylabel('Drawdown (%)')
    plt.grid(True)
    plt.savefig("results/backtest/drawdown_curve.png")
    plt.show()
    
    print(f"回测完成，最终资金: {final_capital:.2f} USDT")
    print(f"总收益率: {metrics_dict['total_return']:.2%}")
    print(f"夏普比率: {metrics_dict['sharpe_ratio']:.2f}")
    print(f"最大回撤: {metrics_dict['max_drawdown']:.2%}")

if __name__ == "__main__":
    main()