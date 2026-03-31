import json
import time
import websocket
from web3 import Web3
from web3.middleware import geth_poa_middleware

def listen_paxg_transfers(ws_url, on_transfer):
    """
    监听 PAXG Transfer 事件
    on_transfer: 回调函数，接收 (from, to, value, tx_hash, block_number)
    """
    w3 = Web3(Web3.WebsocketProvider(ws_url))
    if not w3.is_connected():
        raise Exception("WebSocket 连接失败")

    # PAXG 合约地址和事件签名
    PAXG_ADDRESS = Web3.to_checksum_address("0x45804880De22913dAFE09f4980848ECE6EcbAf78")
    transfer_topic = Web3.keccak(text="Transfer(address,address,uint256)").hex()

    # 订阅日志
    def handle_log(log):
        if log['address'].lower() != PAXG_ADDRESS.lower():
            return
        if log['topics'][0].hex() != transfer_topic:
            return
        # 解析 from, to, value
        from_addr = Web3.to_checksum_address('0x' + log['topics'][1].hex()[-40:])
        to_addr = Web3.to_checksum_address('0x' + log['topics'][2].hex()[-40:])
        value = int(log['data'], 16) / 1e18
        tx_hash = log['transactionHash'].hex()
        block_number = log['blockNumber']
        on_transfer(from_addr, to_addr, value, tx_hash, block_number)

    # 使用 websocket-client 订阅
    ws = websocket.WebSocketApp(ws_url,
                                on_message=lambda ws, msg: handle_log(json.loads(msg)['params']['result']),
                                on_error=lambda ws, e: print(f"Error: {e}"),
                                on_close=lambda ws, *args: print("WebSocket closed"))
    ws.run_forever()