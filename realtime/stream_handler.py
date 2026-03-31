import json
import os
from datetime import datetime

class StreamHandler:
    def __init__(self, output_file="realtime/predictions.jsonl"):
        self.output_file = output_file
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

    def process(self, tx_data, pred_label, confidence):
        """处理一笔交易"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "transaction_hash": tx_data['tx_hash'],
            "from_addr": tx_data['from_addr'],
            "to_addr": tx_data['to_addr'],
            "value_paxg": tx_data['value'],
            "value_usd": tx_data['value_usd'],
            "predicted_intent": pred_label,
            "confidence": confidence,
            "gold_price": tx_data['gold_price']
        }
        # 保存到文件
        with open(self.output_file, "a") as f:
            f.write(json.dumps(record) + "\n")
        # 打印到控制台
        print(f"[{record['timestamp']}] 交易 {record['transaction_hash'][:10]}... "
              f"预测意图: {pred_label} (置信度: {confidence:.2f})")
        # 这里可扩展推送至看板（例如 WebSocket 或消息队列）