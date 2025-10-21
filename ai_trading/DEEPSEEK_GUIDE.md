# DeepSeek AI 交易机器人使用指南

## 概述

系统已成功从 Anthropic Claude 迁移到 **DeepSeek API**，使用更具成本效益的 AI 模型。

### 🎯 DeepSeek 优势

根据 [DeepSeek API 文档](https://api-docs.deepseek.com/quick_start/pricing#model-details)：

| 特性 | DeepSeek | Anthropic Claude |
|------|----------|------------------|
| **输入价格** | $0.28/M tokens | ~$3.00/M tokens |
| **输出价格** | $0.42/M tokens | ~$15.00/M tokens |
| **成本优势** | **便宜 10-35 倍** | - |
| **推理模式** | ✅ deepseek-reasoner | - |
| **上下文长度** | 128K | 200K |

## 可用模型

### 1. `deepseek-chat` (非思考模式)
- 快速响应
- 适合简单决策
- 较低延迟

### 2. `deepseek-reasoner` (思考模式) ⭐ 推荐
- 深度推理能力
- 更准确的交易决策
- 适合复杂市场分析

## 快速开始

### 方法 1: 使用启动脚本（最简单）

```bash
# 测试模式（只运行一次）
./ai_trading/start_deepseek.sh --test

# 正常模式（持续运行）
./ai_trading/start_deepseek.sh
```

### 方法 2: 手动运行

```bash
# 设置 API Key
export DEEPSEEK_API_KEY='sk-b14ed35ef1564874952a45ff819f2f7a'

# 激活虚拟环境
source venv/bin/activate

# 运行交易机器人
python ai_trading/ai_trader_bot.py \
    --model deepseek-reasoner \
    --coins BTC ETH SOL \
    --interval 3 \
    --testnet
```

## 命令行参数

```bash
python ai_trading/ai_trader_bot.py [选项]

选项:
  --model MODEL           DeepSeek 模型选择
                          可选: deepseek-chat, deepseek-reasoner
                          默认: deepseek-reasoner
  
  --coins COIN [COIN ...] 交易的币种列表
                          默认: BTC ETH SOL
  
  --interval N            交易间隔（分钟）
                          默认: 3
  
  --testnet               使用测试网（默认）
  
  --test                  测试模式（只运行一次）
  
  --api-key KEY           DeepSeek API Key
                          （或使用环境变量 DEEPSEEK_API_KEY）
```

## 使用示例

### 示例 1: 测试模式
```bash
export DEEPSEEK_API_KEY='your-api-key'
python ai_trading/ai_trader_bot.py --test
```

### 示例 2: 自定义币种
```bash
python ai_trading/ai_trader_bot.py \
    --model deepseek-reasoner \
    --coins BTC ETH BNB DOGE \
    --interval 5
```

### 示例 3: 使用 deepseek-chat（更快）
```bash
python ai_trading/ai_trader_bot.py \
    --model deepseek-chat \
    --coins BTC ETH \
    --interval 1
```

## 配置文件

编辑 `ai_trading/config.json.example` 并保存为 `config.json`：

```json
{
  "coins": ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE"],
  "interval_minutes": 3,
  "use_testnet": true,
  "initial_capital": 10000.0,
  "ai_model": {
    "provider": "deepseek",
    "model": "deepseek-reasoner",
    "temperature": 0.7,
    "max_tokens": 4096
  }
}
```

## 运行测试

### 完整系统测试
```bash
source venv/bin/activate
export DEEPSEEK_API_KEY='your-api-key'
python ai_trading/test_system.py
```

### 测试结果示例
```
✅ 模块导入
✅ Hyperliquid 连接
✅ 市场数据获取
✅ Prompt 构建
✅ DeepSeek API

🎉 所有测试通过！
```

## 成本估算

基于 [DeepSeek 定价](https://api-docs.deepseek.com/quick_start/pricing#model-details)：

### 每次交易循环
- 输入: ~2,000 tokens (Prompt)
- 输出: ~500 tokens (决策)
- **成本**: ~$0.00077 per cycle

### 每日成本（每3分钟一次）
- 480 次循环/天
- **总成本**: ~$0.37/天
- **月成本**: ~$11/月

对比 Anthropic Claude：
- Claude 月成本: ~$150-300/月
- **节省**: 90%+ 💰

## 监控和日志

### 查看实时日志
交易机器人会输出详细日志：
- 市场价格和指标
- AI 决策理由
- 订单执行结果
- 账户盈亏情况

### 保存的文件
- `ai_trading/last_prompt.txt` - 最后一次发送的 Prompt
- `ai_trading/last_decision.json` - AI 的最后决策

## 故障排除

### 问题 1: API Key 错误
```bash
# 检查环境变量
echo $DEEPSEEK_API_KEY

# 重新设置
export DEEPSEEK_API_KEY='your-api-key'
```

### 问题 2: 连接超时
- 检查网络连接
- 确认 API Key 有效
- 查看 [DeepSeek API 状态](https://status.deepseek.com)

### 问题 3: 模型响应格式错误
- 查看 `ai_trading/last_prompt.txt`
- 检查 Prompt 格式
- 尝试使用 `deepseek-chat` 模型

## 技术实现细节

### API 调用
使用 OpenAI SDK 兼容接口：

```python
from openai import OpenAI

client = OpenAI(
    api_key="your-api-key",
    base_url="https://api.deepseek.com"
)

response = client.chat.completions.create(
    model="deepseek-reasoner",
    messages=[
        {"role": "system", "content": "You are a trading AI..."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.7,
    max_tokens=4096
)
```

### 代码改动
1. ✅ 替换 `anthropic` → `openai` SDK
2. ✅ 更新 API 调用方式
3. ✅ 修改配置文件格式
4. ✅ 更新测试脚本
5. ✅ 添加模型选择参数

## 性能建议

### 推荐配置
```bash
# 平衡性能和成本
--model deepseek-reasoner
--interval 3
--coins BTC ETH SOL  # 3-5 个币种
```

### 高频交易
```bash
# 使用更快的模型
--model deepseek-chat
--interval 1
```

### 深度分析
```bash
# 使用推理模型
--model deepseek-reasoner
--interval 5
```

## 参考资源

- [DeepSeek API 文档](https://api-docs.deepseek.com/)
- [DeepSeek 定价](https://api-docs.deepseek.com/quick_start/pricing)
- [Hyperliquid 文档](https://hyperliquid.gitbook.io/)

## 支持

如有问题，请：
1. 查看日志输出
2. 运行测试: `python ai_trading/test_system.py`
3. 检查配置文件
4. 查看 DeepSeek API 状态

---

**注意**: 始终在测试网上先测试，确认策略有效后再使用主网！

