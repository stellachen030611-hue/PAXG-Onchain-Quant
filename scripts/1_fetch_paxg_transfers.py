import os
import json
import time
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

RPC_URL = os.getenv("ETH_RPC_URL")
if not RPC_URL:
    raise Exception("请在 .env 中设置 ETH_RPC_URL")

w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={'timeout': 60}))

if not w3.is_connected():
    raise Exception("RPC 连接失败，请检查网络或 URL")

print(f"已连接，当前区块: {w3.eth.block_number}")

# PAXG 合约地址
PAXG_ADDRESS = "0x45804880De22913dAFE09f4980848ECE6EcbAf78"

# ERC20 Transfer 事件 ABI
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

contract = w3.eth.contract(address=PAXG_ADDRESS, abi=transfer_abi)

# ================= 配置区 =================
TEST_MODE = True               # True: 测试模式（抓取最近1000个区块）; False: 全量模式
START_BLOCK = 18900000         # 全量模式起始区块（约2024年1月）
TEST_RANGE = 1000              # 测试模式下抓取最近多少个区块
CHUNK_SIZE = 10                # 每次请求的区块数
SLEEP_SEC = 0.5                # 每次请求后休眠秒数
# =========================================

def to_standard_hex(hash_val):
    """将 HexBytes 或 bytes 转为无0x小写十六进制字符串"""
    if isinstance(hash_val, bytes):
        return hash_val.hex()
    s = str(hash_val).lower()
    if s.startswith('0x'):
        s = s[2:]
    return s

latest = w3.eth.block_number

if TEST_MODE:
    from_block = latest - TEST_RANGE
    to_block = latest
    print(f"【测试模式】抓取最近 {TEST_RANGE} 个区块: {from_block} 到 {to_block}")
else:
    if START_BLOCK >= latest:
        raise Exception(f"起始区块 {START_BLOCK} 大于最新区块 {latest}，请减小 START_BLOCK")
    from_block = START_BLOCK
    to_block = latest
    print(f"【全量模式】抓取从 {from_block} 到 {to_block} 的区块（共 {to_block - from_block + 1} 个）")

events = []
for start in range(from_block, to_block + 1, CHUNK_SIZE):
    end = min(start + CHUNK_SIZE - 1, to_block)
    try:
        logs = contract.events.Transfer.get_logs(from_block=start, to_block=end)
        events.extend(logs)
        print(f"已抓取区块 {start}~{end}，本批 {len(logs)} 个事件，累计 {len(events)}")
        time.sleep(SLEEP_SEC)
    except Exception as e:
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"抓取区块 {start}~{end} 失败: {e.response.text}")
        else:
            print(f"抓取区块 {start}~{end} 失败: {e}")
        continue

print(f"总共获取 {len(events)} 个事件")

# 保存原始数据，标准化 transactionHash
output_dir = "data/raw"
os.makedirs(output_dir, exist_ok=True)

events_serializable = []
for ev in events:
    ev_dict = dict(ev)
    ev_dict['args'] = {k: str(v) for k, v in ev['args'].items()}
    # 标准化交易哈希
    ev_dict['transactionHash'] = to_standard_hex(ev['transactionHash'])
    events_serializable.append(ev_dict)

output_file = os.path.join(output_dir, "paxg_transfers.json")
with open(output_file, "w") as f:
    json.dump(events_serializable, f, indent=2, default=str)

print(f"数据已保存到 {output_file}")