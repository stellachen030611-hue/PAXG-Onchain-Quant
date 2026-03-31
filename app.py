"""
app.py
Streamlit 看板 - 量化因子与标注数据展示（示例版本）
"""
import os
import pandas as pd
import streamlit as st
import plotly.express as px

# 定义数据路径
FULL_DATA_PATH = "data/labeled/full_labeled.parquet"
SAMPLE_DATA_PATH = "data/sample/sample_labeled.parquet"

# 加载数据
if os.path.exists(FULL_DATA_PATH):
    df = pd.read_parquet(FULL_DATA_PATH)
    st.sidebar.success("✅ 使用完整标注数据集")
else:
    if os.path.exists(SAMPLE_DATA_PATH):
        df = pd.read_parquet(SAMPLE_DATA_PATH)
        st.sidebar.warning("📊 使用示例数据（50条），如需完整数据请运行脚本生成")
    else:
        st.error("未找到数据文件，请先运行脚本生成数据")
        st.stop()

# 页面配置
st.set_page_config(page_title="PAXG 量化看板", layout="wide")
st.title("🔍 PAXG 链上交易因子与 AI 标注看板")
st.markdown("基于链上黄金代币 PAXG 的量化因子挖掘与 AI 标注分析")

# ==================== 加载数据 ====================
@st.cache_data
def load_labeled_data():
    path = "data/labeled/full_labeled.parquet"
    if os.path.exists(path):
        return pd.read_parquet(path)
    else:
        st.warning("未找到标注数据集，请先运行 6_build_dataset.py 生成 full_labeled.parquet")
        return pd.DataFrame()

@st.cache_data
def load_feature_importance():
    path = "results/feature_importance_intent.csv"
    if os.path.exists(path):
        return pd.read_csv(path)
    else:
        return pd.DataFrame()

df = load_labeled_data()
imp_df = load_feature_importance()

# ==================== 侧边栏筛选 ====================
st.sidebar.header("筛选与配置")
if not df.empty:
    intent_filter = st.sidebar.multiselect(
        "选择意图标签",
        options=df['label_intent'].unique(),
        default=df['label_intent'].unique()
    )
    filtered_df = df[df['label_intent'].isin(intent_filter)]
else:
    filtered_df = df

# ==================== 主要指标 ====================
st.header("📊 数据概览")
if not df.empty:
    col1, col2, col3 = st.columns(3)
    col1.metric("总标注交易数", len(df))
    col2.metric("意图类别数", df['label_intent'].nunique())
    col3.metric("测试集准确率（上次模型）", "59%" if len(df) >= 30 else "待更新")
else:
    st.info("暂无标注数据，请先运行标注流程。")

# ==================== 标签分布 ====================
if not df.empty:
    st.subheader("🏷️ 标注意图分布")
    fig = px.bar(df['label_intent'].value_counts().reset_index(),
                 x='label_intent', y='count', color='label_intent',
                 title="各意图标签数量")
    st.plotly_chart(fig, use_container_width=True)

# ==================== 特征重要性展示 ====================
if not imp_df.empty:
    st.subheader("🔑 特征重要性（随机森林）")
    # 取前10
    top10 = imp_df.head(10)
    fig2 = px.bar(top10, x='importance', y='feature', orientation='h',
                  title="Top 10 特征重要性", text='importance')
    fig2.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("暂无特征重要性数据，请先运行 8_factor_mining.py 生成。")

# ==================== 交易数据预览 ====================
if not filtered_df.empty:
    st.subheader("📝 最近交易记录")
    st.dataframe(filtered_df[['transactionHash', 'value_usd', 'hour', 'day_of_week', 'label_intent']].head(20))

# ==================== 简单策略模拟（占位） ====================
st.sidebar.markdown("---")
st.sidebar.info("后续可添加：实时链上数据、模型在线预测、策略回测结果展示等")