import pandas as pd
import joblib
import numpy as np

class Predictor:
    def __init__(self, model_path):
        self.model = joblib.load(model_path)
        # 尝试获取模型训练时的特征列名
        if hasattr(self.model, 'feature_names_in_'):
            self.feature_names = self.model.feature_names_in_
        else:
            # 若模型无此属性，则根据训练脚本手动指定（与 8_factor_mining.py 保持一致）
            self.feature_names = [
                'value', 'value_usd', 'from_balance_prior', 'to_balance_prior',
                'hour', 'day_of_week', 'gold_price_at_tx', 'gold_price_change_1h',
                'from_total_out', 'to_total_in'
            ]

    def predict(self, features_dict):
        """
        输入特征字典，返回预测标签和置信度
        features_dict: 字典，键为特征名，值为数值
        """
        # 转为 DataFrame
        df = pd.DataFrame([features_dict])
        # 确保所有特征列都存在，缺失的补默认值（0）
        for col in self.feature_names:
            if col not in df.columns:
                df[col] = 0.0
        # 按模型训练时的顺序提取特征
        X = df[self.feature_names].values
        # 预测
        pred_label = self.model.predict(X)[0]
        # 获取概率（如果是分类器）
        if hasattr(self.model, 'predict_proba'):
            proba = self.model.predict_proba(X)[0]
            confidence = np.max(proba)
        else:
            confidence = 1.0
        return pred_label, confidence