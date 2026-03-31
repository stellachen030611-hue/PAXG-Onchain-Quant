import pandas as pd
import numpy as np

def run_backtest(df, config):
    """
    逐笔模拟交易，返回资金曲线和交易记录
    """
    capital = config.INITIAL_CAPITAL
    position = 0.0          # 持有 PAXG 数量
    equity_curve = []       # 权益曲线（时间戳，权益）
    trades = []             # 交易记录（时间戳，类型，价格，数量，金额，权益）

    # 按时间顺序处理
    df_sorted = df.sort_values('timestamp').reset_index(drop=True)
    
    for idx, row in df_sorted.iterrows():
        price = row['gold_price_at_tx']   # 假设 PAXG 价格与黄金价格挂钩，实际应使用 PAXG/USD 价格
        signal = row['signal']
        
        # 计算当前权益 = 现金 + 持仓价值
        equity = capital + position * price
        equity_curve.append((row['timestamp'], equity))
        
        if signal == 1 and capital >= price * config.MIN_TRADE_VALUE:
            # 买入信号：用全部现金买入（或固定比例，此处简化用全部现金）
            amount_to_buy = capital / price
            # 扣除手续费和滑点
            cost = amount_to_buy * price * (1 + config.COMMISSION_RATE + config.SLIPPAGE)
            if cost <= capital:
                capital -= cost
                position += amount_to_buy
                trades.append({
                    'timestamp': row['timestamp'],
                    'type': 'BUY',
                    'price': price,
                    'amount': amount_to_buy,
                    'cost': cost,
                    'equity': equity
                })
        elif signal == -1 and position > 0:
            # 卖出信号：清仓
            amount_to_sell = position
            revenue = amount_to_sell * price * (1 - config.COMMISSION_RATE - config.SLIPPAGE)
            capital += revenue
            position = 0
            trades.append({
                'timestamp': row['timestamp'],
                'type': 'SELL',
                'price': price,
                'amount': amount_to_sell,
                'revenue': revenue,
                'equity': equity
            })
    
    # 最终清仓（如果有持仓）
    if position > 0:
        last_price = df_sorted.iloc[-1]['gold_price_at_tx']
        revenue = position * last_price * (1 - config.COMMISSION_RATE - config.SLIPPAGE)
        capital += revenue
        trades.append({
            'timestamp': df_sorted.iloc[-1]['timestamp'],
            'type': 'SELL (final)',
            'price': last_price,
            'amount': position,
            'revenue': revenue,
            'equity': capital
        })
        position = 0
        equity_curve.append((df_sorted.iloc[-1]['timestamp'], capital))
    
    # 构建权益曲线 DataFrame
    equity_df = pd.DataFrame(equity_curve, columns=['timestamp', 'equity'])
    equity_df.set_index('timestamp', inplace=True)
    
    trades_df = pd.DataFrame(trades) if trades else pd.DataFrame()
    
    return equity_df, trades_df, capital