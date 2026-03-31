# 🥇 PAXG On-Chain Quant: AI-Powered Behavior Labeling & Factor Mining

> 基于链上黄金代币 PAXG 的量化研究作品集 —— 从链上数据采集、本地大模型自动标注，到因子挖掘、策略回测与实时预测，构建完整 AI+量化+Web3 解决方案。

[![Python 3.10](https://img.shields.io/badge/Python-3.10-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28-red.svg)](https://streamlit.io/)
[![Ollama](https://img.shields.io/badge/Ollama-Gemma3:4b-green.svg)](https://ollama.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📌 项目背景

PAXG 是由 Paxos 发行的以太坊上的黄金锚定代币，每枚代币对应一金衡盎司的伦敦合格交割黄金。链上转账行为可能隐含大户的积累(accumulation)或派发(distribution)意图，这些意图往往领先于黄金现货价格的变化。

本项目构建了一条完整的AI+量化+Web3流水线：
- 抓取 PAXG 全量转账记录（26,722 条）
- 使用本地大模型（Ollama + Gemma3:4b）自动标注 2,000+ 条数据的交易意图
- 训练随机森林模型预测意图，输出可解释的特征重要性
- 回测验证意图信号与黄金价格变化的相关性
- 部署 Streamlit 交互看板，实时展示数据、模型与回测结果
- 支持实时监听链上转账，在线预测并可视化

## 🧠 核心亮点

- 端到端链上数据处理：从 RPC 到特征工程，完全自动化。
- 低成本 AI 标注：本地运行 4B 参数模型，无 API 费用，支持断点续传。
- 可解释的量化因子：随机森林输出特征重要性，揭示哪些链上字段影响大资金行为。
- 策略验证框架：回测脚本验证积累/派发信号对未来收益的预测能力。
- 实时预测能力：WebSocket 监听 PAXG 转账，实时调用模型预测意图。
- 交互式看板：多页面 Streamlit 应用，展示数据、因子、回测与实时预测。

## 🗂️ 项目架构
PAXG-Onchain-Quant/
├── data/
│   ├── raw/                  # 原始数据（不变）
│   ├── processed/            # 特征表、标注JSON等（不变）
│   ├── labeled/              # 拆分后的训练/验证/测试集（不变）
│   └── realtime/             # 新增：实时预测记录
│       └── predictions.csv
├── scripts/                  # 保留原有脚本
├── models/                   # 模型文件
├── results/
│   ├── backtest/             # 新增：回测结果
│   │   ├── equity_curve.png
│   │   └── metrics.json
│   └── feature_importance_intent.csv
├── realtime/                 # 新增：实时监听与预测模块
│   ├── listener.py
│   ├── predictor.py
│   └── stream_handler.py
├── backtest/                 # 新增：回测模块
│   ├── engine.py
│   ├── signals.py
│   └── metrics.py
├── app.py                    # 看板（增加页面）
├── requirements.txt
└── README.md

详细目录说明见 [项目结构] 章节。

## 🚀 环境准备

```bash
conda create -n web3-gold python=3.10
conda activate web3-gold
pip install -r requirements.txt