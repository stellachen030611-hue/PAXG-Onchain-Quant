"""
8_factor_mining.py
使用标注数据集训练简单分类模型，输出特征重要性（候选因子）
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os

# ==================== 配置 ====================
LABELED_FILE = "data/labeled/full_labeled.parquet"
MODEL_SAVE_PATH = "models/factor_model_intent.pkl"
FEATURE_IMPORTANCE_PATH = "results/feature_importance_intent.csv"
RANDOM_STATE = 42
TEST_SIZE = 0.2
# =============================================

# 加载数据
print("加载标注数据集...")
df = pd.read_parquet(LABELED_FILE)
print(f"数据集形状: {df.shape}")
print(f"标签分布:\n{df['label_intent'].value_counts()}")

# 定义特征列：排除 ID 类、地址、时间戳以及标签列
exclude_cols = [
    'transactionHash', 'transactionHash_hex', 'from_addr', 'to_addr', 'timestamp',
    'label_intent', 'label_impact', 'label_trend', 'blockNumber', 'logIndex'
]
# 自动获取所有数值型列
feature_cols = [col for col in df.columns if col not in exclude_cols and pd.api.types.is_numeric_dtype(df[col])]
print(f"使用的特征列 ({len(feature_cols)}): {feature_cols}")

X = df[feature_cols].copy()
y = df['label_intent'].copy()   # 先用意图标签作为目标

# 处理缺失值（简单用中位数填充）
X = X.fillna(X.median())

# 划分数据集（按时间排序，模拟时序场景）
df_sorted = df.sort_values('timestamp')
split_idx = int(len(df_sorted) * (1 - TEST_SIZE))
X_train = X.iloc[:split_idx]
X_test = X.iloc[split_idx:]
y_train = y.iloc[:split_idx]
y_test = y.iloc[split_idx:]

# 若测试集为空，则调整划分
if X_test.shape[0] == 0:
    print("测试集为空，将使用全量数据训练（无测试）")
    X_test = X_train
    y_test = y_train

print(f"训练集大小: {X_train.shape[0]}, 测试集大小: {X_test.shape[0]}")

# 训练模型
print("\n训练随机森林模型...")
model = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=RANDOM_STATE, n_jobs=-1)
model.fit(X_train, y_train)

# 评估
y_pred = model.predict(X_test)
acc = accuracy_score(y_test, y_pred)
print(f"\n测试集准确率: {acc:.4f}")
print("\n分类报告:")
print(classification_report(y_test, y_pred, zero_division=0))

# 特征重要性
importance_df = pd.DataFrame({
    'feature': feature_cols,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print("\n特征重要性 Top 10:")
print(importance_df.head(10))

# 保存结果
os.makedirs("models", exist_ok=True)
os.makedirs("results", exist_ok=True)
joblib.dump(model, MODEL_SAVE_PATH)
importance_df.to_csv(FEATURE_IMPORTANCE_PATH, index=False)
print(f"\n模型已保存至: {MODEL_SAVE_PATH}")
print(f"特征重要性已保存至: {FEATURE_IMPORTANCE_PATH}")