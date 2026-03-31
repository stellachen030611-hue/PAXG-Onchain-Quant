import pandas as pd
import requests
import json
import time
import os
import ast

# ==================== 辅助函数 ====================
def normalize_hash(hash_val):
    """将任意格式哈希转为无0x小写十六进制字符串"""
    if isinstance(hash_val, bytes):
        return hash_val.hex()
    s = str(hash_val).strip()
    if (s.startswith("b'") and s.endswith("'")) or (s.startswith('b"') and s.endswith('"')):
        try:
            s_escaped = s.replace('\n', '\\n').replace('\r', '\\r')
            obj = ast.literal_eval(s_escaped)
            if isinstance(obj, bytes):
                return obj.hex()
        except Exception:
            pass
    if s.startswith('0x'):
        s = s[2:]
    return s.lower()

# ==================== 配置 ====================
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma3:4b"
SAMPLE_SIZE = 500  ##测试数据量 后增量500-2000
RETRY = 2
TIMEOUT = 120

FEATURE_FILE = "data/processed/paxg_transactions.parquet"
CHECKPOINT_FILE = "data/processed/labeled_tasks_checkpoint.json"
OUTPUT_FILE = "data/processed/labeled_tasks.json"
# =============================================

def query_ollama(prompt):
    for attempt in range(RETRY + 1):
        try:
            response = requests.post(
                OLLAMA_URL,
                json={"model": MODEL, "prompt": prompt, "stream": False, "options": {"temperature": 0}},
                timeout=TIMEOUT
            )
            response.raise_for_status()
            return response.json().get("response", "").strip()
        except Exception as e:
            if attempt < RETRY:
                print(f"    请求失败，重试 {attempt+1}/{RETRY}... 错误: {e}")
                time.sleep(5)
            else:
                print(f"    请求最终失败: {e}")
                return ""

def parse_labels(output):
    intent = "normal"
    impact = "medium_impact"
    trend = "neutral"
    for line in output.split('\n'):
        line = line.strip()
        if line.startswith("Intent:"):
            intent = line.split(":", 1)[1].strip().lower()
        elif line.startswith("Impact:"):
            impact = line.split(":", 1)[1].strip().lower()
        elif line.startswith("Trend:"):
            trend = line.split(":", 1)[1].strip().lower()
    if intent not in ["accumulation", "distribution", "arbitrage", "normal"]:
        intent = "normal"
    if impact not in ["high_impact", "medium_impact", "low_impact"]:
        impact = "medium_impact"
    if trend not in ["trend_following", "contrarian", "neutral"]:
        trend = "neutral"
    return intent, impact, trend

def get_labels(row):
    prompt = f"""Classify this PAXG transaction.

From: {row['from_addr'][:10]}...{row['from_addr'][-6:]}
To: {row['to_addr'][:10]}...{row['to_addr'][-6:]}
Amount: {row['value']:.2f} PAXG
Gold price: ${row['gold_price_at_tx']:.2f}
1h price change: {row['gold_price_change_1h']:.1f}%
Value: ${row['value_usd']:.0f}

Output three labels:
Intent: [accumulation/distribution/arbitrage/normal]
Impact: [high_impact/medium_impact/low_impact]
Trend: [trend_following/contrarian/neutral]

Format exactly as:
Intent: X
Impact: Y
Trend: Z
"""
    output = query_ollama(prompt)
    return parse_labels(output)

# ==================== 主程序 ====================
if __name__ == "__main__":
    # 1. 加载特征数据
    print("加载特征表...")
    df = pd.read_parquet(FEATURE_FILE)
    # 确保有标准化哈希列
    if 'transactionHash_hex' not in df.columns:
        print("特征表中没有 transactionHash_hex 列，正在创建...")
        df['transactionHash_hex'] = df['transactionHash'].apply(normalize_hash)
    print(f"特征表共 {len(df)} 行")

    # 2. 加载已有标注（检查点）
    processed_hashes = set()
    existing_tasks = []
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            existing_tasks = json.load(f)
            processed_hashes = {t["data"]["transaction_hash"] for t in existing_tasks}
        print(f"从检查点加载了 {len(processed_hashes)} 条已标注记录")
    else:
        print("未找到检查点文件，从头开始")

    # 3. 筛选未标注的交易
    df_unlabeled = df[~df['transactionHash_hex'].isin(processed_hashes)].copy()
    print(f"剩余未标注交易数: {len(df_unlabeled)}")

    if len(df_unlabeled) == 0:
        print("所有交易均已标注，无需处理")
        exit(0)

    sample_size = min(SAMPLE_SIZE, len(df_unlabeled))
    df_sample = df_unlabeled.sample(n=sample_size, random_state=42)
    print(f"本次将处理 {len(df_sample)} 条新记录，模型: {MODEL}")

    # 4. 处理新记录并实时保存检查点
    new_tasks = []
    for idx, row in df_sample.iterrows():
        tx_hash_hex = row['transactionHash_hex']   # 已是标准十六进制
        print(f"处理交易 {tx_hash_hex} ...", end="")
        intent, impact, trend = get_labels(row)
        print(f" 完成 -> Intent: {intent}, Impact: {impact}, Trend: {trend}")

        text = f"""
From: {row['from_addr'][:10]}...{row['from_addr'][-6:]}
To: {row['to_addr'][:10]}...{row['to_addr'][-6:]}
Amount: {row['value']:.4f} PAXG
Gold price at time: ${row['gold_price_at_tx']:.2f}
1h price change: {row['gold_price_change_1h']:.2f}%
Transaction value: ${row['value_usd']:.2f}
LLM predictions: Intent={intent}, Impact={impact}, Trend={trend}
"""
        task = {
            "data": {
                "text": text,
                "transaction_hash": tx_hash_hex,          # 标准十六进制
                "transaction_hash_raw": row['transactionHash'],
                "llm_intent": intent,
                "llm_impact": impact,
                "llm_trend": trend
            },
            "annotations": [{
                "result": [
                    {"from_name": "intent", "value": {"choices": [intent]}},
                    {"from_name": "impact", "value": {"choices": [impact]}},
                    {"from_name": "trend", "value": {"choices": [trend]}}
                ]
            }]
        }
        new_tasks.append(task)

        # 实时保存检查点
        all_tasks = existing_tasks + new_tasks
        with open(CHECKPOINT_FILE, "w") as f:
            json.dump(all_tasks, f, indent=2)
        print(f"  已保存检查点，累计 {len(all_tasks)} 条")

    # 5. 合并并保存最终文件
    all_tasks = existing_tasks + new_tasks
    with open(OUTPUT_FILE, "w") as f:
        json.dump(all_tasks, f, indent=2)

    print(f"全部完成！共生成 {len(all_tasks)} 条标注，保存至 {OUTPUT_FILE}")