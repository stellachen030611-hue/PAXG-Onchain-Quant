import pandas as pd
import numpy as np

def generate_signals(df, model, config):
    """
    输入：
        df: 特征表（含时间戳、金额、黄金价格等）
        model: 训练好的分类模型（如随机森林）
        config: 配置对象（包含阈值、意图列表等）
    输出：
        df_with_signals: 添加 signal 列（1=买入，-1=卖出，0=无操作）
    """
    # 1. 使用模型预测所有交易的意图标签
    # 定义排除列（必须与训练时一致，参考 8_factor_mining.py）
    exclude_cols = [
        'transactionHash', 'transactionHash_hex', 'from_addr', 'to_addr', 'timestamp',
        'label_intent', 'label_impact', 'label_trend', 'blockNumber', 'logIndex'
    ]
    # 选择数值型且不在排除列表中的列作为特征
    feature_cols = [col for col in df.columns if col not in exclude_cols and pd.api.types.is_numeric_dtype(df[col])]
    
    # 提取特征并填充缺失值（与训练时一致）
    X = df[feature_cols].copy()
    X = X.fillna(X.median())
    
    # 预测
    df['pred_intent'] = model.predict(X)
    
    # 2. 计算黄金价格均线（用于趋势过滤）
    if config.FILTER_BY_GOLD_TREND:
        # 使用 gold_price_at_tx 列计算滚动均线
        df['gold_ma'] = df['gold_price_at_tx'].rolling(config.GOLD_MA_WINDOW, min_periods=1).mean()
        df['gold_trend_up'] = df['gold_price_at_tx'] > df['gold_ma']
    else:
        df['gold_trend_up'] = True  # 默认认为趋势向上
    
    # 3. 生成信号
    df['signal'] = 0
    # 买入：意图为买入类 + 交易金额超阈值 + （可选）黄金趋势向上
    buy_condition = (df['pred_intent'].isin(config.BUY_INTENTS)) & \
                    (df['value_usd'] >= config.MIN_TRADE_VALUE) & \
                    (df['gold_trend_up'])
    df.loc[buy_condition, 'signal'] = 1
    
    # 卖出：意图为卖出类 + 交易金额超阈值（卖出不需要趋势过滤）
    sell_condition = (df['pred_intent'].isin(config.SELL_INTENTS)) & \
                     (df['value_usd'] >= config.MIN_TRADE_VALUE)
    df.loc[sell_condition, 'signal'] = -1
    
    return df