import sys
import os
import time
import pandas as pd
from web3 import Web3
from dotenv import load_dotenv

# 将项目根目录加入模块搜索路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realtime import config, state_cache, feature_extractor, predictor, stream_handler

load_dotenv()

def main():
    # 1. 连接 RPC
    RPC_URL = os.getenv("ETH_RPC_URL")
    if not RPC_URL:
        raise Exception("请在 .env 中设置 ETH_RPC_URL")
    w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={'timeout': 60}))
    if not w3.is_connected():
        raise Exception("RPC 连接失败，请检查网络或 URL")
    print("RPC 连接成功")
    PAXG_ADDRESS_CHECKSUM = Web3.to_checksum_address(config.PAXG_ADDRESS)

    # 2. 初始化状态缓存
    cache = state_cache.StateCache()

    # 3. 加载历史特征表，预填充地址余额
    print("加载历史特征表...")
    df_hist = pd.read_parquet(config.FEATURE_TABLE_PATH)
    # 从历史表中计算每个地址的累计流入/流出
    for _, row in df_hist.iterrows():
        from_addr = row['from_addr']
        to_addr = row['to_addr']
        value = row['value']
        # 更新发送方流出
        cache.update_address_balance(from_addr, value, is_incoming=False)
        # 更新接收方流入
        cache.update_address_balance(to_addr, value, is_incoming=True)
    print(f"加载历史地址数: 发送方 {len(cache.address_outflow)}, 接收方 {len(cache.address_inflow)}")

    # 4. 加载模型
    print("加载模型...")
    pred = predictor.Predictor(config.MODEL_PATH)

    # 5. 初始化流处理器
    handler = stream_handler.StreamHandler()

    # 6. 获取起始区块（从最新区块开始）
    last_block = w3.eth.block_number
    print(f"开始监听，起始区块: {last_block}")

    # 黄金价格定时更新
    last_gold_update = 0

    def on_transfer(from_addr, to_addr, value, tx_hash, block_number):
        """处理一笔新交易"""
        nonlocal last_gold_update
        # 更新黄金价格（每隔一段时间）
        now = time.time()
        if now - last_gold_update > config.GOLD_PRICE_UPDATE_INTERVAL:
            gold_price = feature_extractor.get_current_gold_price()
            cache.set_gold_price(gold_price)
            last_gold_update = now
        gold_price = cache.get_gold_price()
        if gold_price is None:
            gold_price = 400.0  # 默认

        # 提取特征
        tx_data = {
            'from_addr': from_addr,
            'to_addr': to_addr,
            'value': value,
            'timestamp': pd.Timestamp.now(),  # 近似
            'tx_hash': tx_hash,
            'gold_price': gold_price,
            'value_usd': value * gold_price
        }
        features = feature_extractor.compute_features(tx_data, cache, gold_price)
        # 预测
        label, confidence = pred.predict(features)
        # 添加金额信息到 tx_data 用于记录
        tx_data['value_usd'] = value * gold_price
        # 处理结果
        handler.process(tx_data, label, confidence)

        # 更新缓存（该交易完成后，更新地址余额）
        cache.update_address_balance(from_addr, value, is_incoming=False)
        cache.update_address_balance(to_addr, value, is_incoming=True)
    
    # 定义 Transfer 事件的 ABI（可在文件开头定义一次）
    transfer_abi = [
        {
            "anonymous": False,
            "inputs": [
                {"indexed": True, "name": "from", "type": "address"},
                {"indexed": True, "name": "to", "type": "address"},
                {"indexed": False, "name": "value", "type": "uint256"}
            ],
            "name": "Transfer",
            "type": "event"
        }
    ]

    # 轮询新区块
    while True:
        current_block = w3.eth.block_number
        if current_block > last_block:
            from_block = last_block + 1
            to_block = current_block
            print(f"处理区块 {from_block} 到 {to_block} ...")
            logs = w3.eth.get_logs({
                'fromBlock': from_block,
                'toBlock': to_block,
                'address': PAXG_ADDRESS_CHECKSUM,
                'topics': [config.TRANSFER_TOPIC]
            })
            for log in logs:
                # 解码事件
                contract = w3.eth.contract(address=PAXG_ADDRESS_CHECKSUM, abi=transfer_abi)
                decoded = contract.events.Transfer().process_log(log)
                from_addr = decoded['args']['from']
                to_addr = decoded['args']['to']
                value = decoded['args']['value'] / 1e18
                tx_hash = log['transactionHash'].hex()
                block_number = log['blockNumber']
                on_transfer(from_addr, to_addr, value, tx_hash, block_number)
            last_block = current_block
        time.sleep(1)



if __name__ == "__main__":
    main()