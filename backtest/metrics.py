import numpy as np
import pandas as pd

def calculate_metrics(equity_series, initial_capital, risk_free_rate=0.02):
    """
    equity_series: 每日权益序列（时间索引）
    initial_capital: 初始资金
    risk_free_rate: 年化无风险利率（例如0.02）
    """
    returns = equity_series.pct_change().dropna()
    
    # 累计收益率
    total_return = (equity_series.iloc[-1] - initial_capital) / initial_capital
    
    # 年化收益率（假设252个交易日）
    days = (equity_series.index[-1] - equity_series.index[0]).days
    if days > 0:
        annual_return = (1 + total_return) ** (365 / days) - 1
    else:
        annual_return = 0
    
    # 年化波动率
    annual_vol = returns.std() * np.sqrt(252)
    
    # 夏普比率
    sharpe = (annual_return - risk_free_rate) / annual_vol if annual_vol > 0 else 0
    
    # 最大回撤
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = drawdown.min()
    
    # 胜率（仅考虑有交易的日子）
    # 这里简化：用收益率>0的天数占比
    win_rate = (returns > 0).sum() / len(returns) if len(returns) > 0 else 0
    
    metrics = {
        'total_return': total_return,
        'annual_return': annual_return,
        'annual_volatility': annual_vol,
        'sharpe_ratio': sharpe,
        'max_drawdown': max_drawdown,
        'win_rate': win_rate,
        'num_trades': len(returns)  # 可改为实际交易次数
    }
    return metrics