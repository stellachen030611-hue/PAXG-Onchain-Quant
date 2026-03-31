# 回测参数
INITIAL_CAPITAL = 100000.0          # 初始资金（USDT）
COMMISSION_RATE = 0.001             # 手续费率（0.1%）
SLIPPAGE = 0.0005                   # 滑点（0.05%）

# 信号生成规则
MIN_TRADE_VALUE = 1000.0            # 最小交易金额阈值（美元）
BUY_INTENTS = ['accumulation']      # 触发买入的意图标签
SELL_INTENTS = ['distribution']     # 触发卖出的意图标签
FILTER_BY_GOLD_TREND = True         # 是否用黄金价格趋势过滤
GOLD_MA_WINDOW = 20                 # 黄金价格均线窗口（分钟）