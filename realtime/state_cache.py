import time
from collections import defaultdict

class StateCache:
    def __init__(self):
        # 地址 -> 累计收到 PAXG 总量（从历史数据+实时流构建）
        self.address_inflow = defaultdict(float)
        self.address_outflow = defaultdict(float)
        # 地址 -> 最后更新时间（区块时间戳）
        self.last_update = {}
        # 黄金价格缓存
        self.gold_price = None
        self.gold_price_timestamp = 0

    def update_address_balance(self, address, amount, is_incoming):
        if is_incoming:
            self.address_inflow[address] += amount
        else:
            self.address_outflow[address] += amount
        self.last_update[address] = time.time()

    def get_balance_prior(self, address, is_sender):
        if is_sender:
            return self.address_outflow[address]
        else:
            return self.address_inflow[address]

    def set_gold_price(self, price):
        self.gold_price = price
        self.gold_price_timestamp = time.time()

    def get_gold_price(self):
        return self.gold_price