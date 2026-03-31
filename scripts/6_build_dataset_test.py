import pandas as pd
import json
import os
from sklearn.model_selection import train_test_split

def normalize_hash(hash_val):
    """与3中保持一致，将任意哈希转为无0x小写十六进制"""
    if isinstance(hash_val, bytes):
        return hash_val.hex()
    s = str(hash_val).strip()
    if s.startswith('0x'):
        s = s[2:]
    return s.lower()

# 加载特征表
parquet_path = "data/processed/paxg_transactions.parquet"
if not os.path.exists(parquet_path):
    raise FileNotFoundError(f"特征文件不存在: {parquet_path}")

df = pd.read_parquet(parquet_path)
print(f"原始特征表共 {len(df)} 行")

# 确保有标准化哈希列
if 'transactionHash_hex' not in df.columns:
    print("特征表中没有 transactionHash_hex 列，正在创建...")
    df['transactionHash_hex'] = df['transactionHash'].apply(normalize_hash)

# 加载标注文件
label_file = "data/processed/labeled_tasks.json"
if not os.path.exists(label_file):
    raise FileNotFoundError(f"标注文件不存在: {label_file}")

print(f"正在从 {label_file} 加载标注...")
with open(label_file, "r", encoding="utf-8") as f:
    labeled_data = json.load(f)

# 构建标签映射
label_map = {}
for item in labeled_data:
    tx_hash = item['data']['transaction_hash']   # 已是标准十六进制
    annotations = item.get('annotations', [])
    if not annotations:
        continue
    result = annotations[0].get('result', [])
    intent = impact = trend = None
    for res in result:
        from_name = res.get('from_name')
        choices = res.get('value', {}).get('choices', [])
        if choices:
            val = choices[0]
            if from_name == 'intent':
                intent = val
            elif from_name == 'impact':
                impact = val
            elif from_name == 'trend':
                trend = val
    if intent and impact and trend:
        label_map[tx_hash] = (intent, impact, trend)

print(f"成功解析 {len(label_map)} 条标注")

# 合并标签
df['label_intent'] = df['transactionHash_hex'].map(lambda x: label_map.get(x, (None, None, None))[0])
df['label_impact'] = df['transactionHash_hex'].map(lambda x: label_map.get(x, (None, None, None))[1])
df['label_trend'] = df['transactionHash_hex'].map(lambda x: label_map.get(x, (None, None, None))[2])

matched = df['label_intent'].notna().sum()
print(f"匹配到的标注记录数: {matched}")

df_labeled = df.dropna(subset=['label_intent']).copy()
print(f"最终标注数据集大小: {len(df_labeled)}")

if len(df_labeled) == 0:
    print("\n[警告] 没有匹配到任何标注！")
    print("特征表前3个哈希样例:", df['transactionHash_hex'].head(3).tolist())
    print("标注映射前3个键样例:", list(label_map.keys())[:3])
    exit(1)

# 划分数据集
train, temp = train_test_split(df_labeled, test_size=0.3, random_state=42)
val, test = train_test_split(temp, test_size=0.5, random_state=42)

# 保存
os.makedirs("data/labeled", exist_ok=True)
df_labeled.to_parquet("data/labeled/full_labeled.parquet", index=False)
train.to_parquet("data/labeled/train.parquet", index=False)
val.to_parquet("data/labeled/val.parquet", index=False)
test.to_parquet("data/labeled/test.parquet", index=False)

print("数据集已成功保存到 data/labeled/")