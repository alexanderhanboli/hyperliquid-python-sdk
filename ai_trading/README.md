# AI 交易机器人系统

这是一个复现 [nof1.ai](https://nof1.ai/) 架构的 AI 交易机器人系统，使用 Claude Sonnet 4.5 作为交易决策引擎。

## 系统架构

```
┌─────────────────┐
│  市场数据模块    │ ← 获取价格、K线数据
│ (market_data.py) │ ← 计算技术指标 (EMA, MACD, RSI, ATR)
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Prompt构建器   │ ← 将市场数据格式化为 AI prompt
│(prompt_builder) │ ← 包含账户信息、持仓状态
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│   AI 模型       │ ← Claude Sonnet 4.5
│  (Anthropic)    │ ← 分析数据并返回交易决策 (JSON)
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  订单执行器     │ ← 解析 AI 决策
│(order_executor) │ ← 执行开仓/平仓/止盈止损
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Hyperliquid    │ ← 实际交易所
│    Exchange     │
└─────────────────┘
```

## 核心流程

1. **数据收集** (每3分钟)
   - 获取所有币种的最新价格
   - 获取 K 线数据 (3分钟、4小时)
   - 计算技术指标 (EMA20, MACD, RSI-7, RSI-14, ATR)

2. **Prompt 构建**
   - 格式化市场数据为 AI 可理解的 prompt
   - 包含当前持仓、账户价值、收益率
   - 提供完整的历史序列数据

3. **AI 决策**
   - Claude 分析市场数据
   - 返回 JSON 格式的交易决策
   - 包含：币种、信号(entry/hold/close)、数量、止盈止损、杠杆等

4. **订单执行**
   - 解析 AI 决策
   - 执行市价开仓/平仓
   - 自动设置止盈止损订单

## 快速开始

### 1. 安装依赖

```bash
pip install anthropic schedule pandas numpy
```

### 2. 配置环境

```bash
# 复制配置文件
cp ai_trading/config.json.example ai_trading/config.json

# 设置 Anthropic API Key
export ANTHROPIC_API_KEY='your-api-key-here'

# 配置 Hyperliquid 钱包 (使用 examples/config.json)
cd examples
cp config.json.example config.json
# 编辑 config.json，填入你的私钥
```

### 3. 测试运行

```bash
# 测试模式：只运行一次
python ai_trading/ai_trader_bot.py --test

# 正常运行：每3分钟执行一次
python ai_trading/ai_trader_bot.py

# 自定义币种和间隔
python ai_trading/ai_trader_bot.py --coins BTC ETH SOL --interval 5
```

## 文件说明

### 核心模块

- **`market_data.py`** - 市场数据获取和技术指标计算
  - `TechnicalIndicators` - 计算 EMA, MACD, RSI, ATR
  - `MarketDataFetcher` - 获取 K 线数据和实时价格

- **`prompt_builder.py`** - AI Prompt 构建器
  - 将市场数据格式化为结构化的 prompt
  - 包含完整的技术指标序列
  - 添加交易指令和规则

- **`order_executor.py`** - 订单执行器
  - 执行开仓、平仓操作
  - 自动设置止盈止损
  - 管理持仓和风险

- **`ai_trader_bot.py`** - 主程序
  - 定时执行交易循环
  - 调用 Claude API
  - 协调各个模块

### 配置文件

- **`config.json`** - 交易配置
  - 交易币种列表
  - 交易间隔
  - 风险参数
  - AI 模型配置

### 输出文件

- **`last_prompt.txt`** - 最后一次发送给 AI 的 prompt（用于调试）
- **`last_decision.json`** - AI 的最新决策（用于调试）

## AI 决策格式

AI 模型会返回如下格式的 JSON：

### 开仓 (Entry)
```json
{
  "BTC": {
    "trade_signal_args": {
      "coin": "BTC",
      "signal": "entry",
      "is_buy": true,
      "quantity": 0.1,
      "profit_target": 110000,
      "stop_loss": 105000,
      "invalidation_condition": "If price closes below 105000",
      "leverage": 10,
      "confidence": 0.75,
      "risk_usd": 500,
      "justification": "RSI oversold at 29, MACD showing bullish divergence..."
    }
  }
}
```

### 持仓 (Hold)
```json
{
  "BTC": {
    "trade_signal_args": {
      "coin": "BTC",
      "signal": "hold",
      "quantity": 0.1,
      "profit_target": 110000,
      "stop_loss": 105000,
      "invalidation_condition": "If price closes below 105000",
      "leverage": 10,
      "confidence": 0.75,
      "risk_usd": 500
    }
  }
}
```

### 平仓 (Close)
```json
{
  "BTC": {
    "trade_signal_args": {
      "coin": "BTC",
      "signal": "close",
      "quantity": 0.1,
      "justification": "Invalidation condition met: price closed below 105000"
    }
  }
}
```

## 交易规则

1. **不允许加仓** - 每个币种只能有一个持仓
2. **必须设置止损** - 每个开仓都需要止损价格
3. **必须设置止盈** - 每个开仓都需要止盈价格
4. **风险收益比** - 至少 1:2
5. **杠杆范围** - 5x 到 40x
6. **最小订单价值** - $10 USD

## 技术指标说明

### EMA (指数移动平均)
- **EMA20** - 20期指数移动平均，用于判断短期趋势

### MACD (指数平滑异同移动平均线)
- 快线 EMA12 - 慢线 EMA26
- 用于判断趋势转折点

### RSI (相对强弱指标)
- **RSI(7)** - 7期 RSI，更敏感
- **RSI(14)** - 14期 RSI，标准周期
- 超买: > 70，超卖: < 30

### ATR (平均真实波幅)
- 衡量市场波动性
- 用于设置止损距离

## 示例场景

### 场景 1: 市场超卖，做多信号

```
当前状态:
- BTC 价格: $107,798
- RSI(7): 29.3 (超卖)
- MACD: 15.8 (下降但仍为正)
- EMA20: $107,919 (价格在 EMA 下方)

AI 决策:
- 信号: ENTRY (做多)
- 入场价: $107,800
- 止损: $105,000 (-2.6%)
- 止盈: $115,000 (+6.7%)
- 杠杆: 10x
- 风险收益比: 1:2.6 ✅
```

### 场景 2: 持仓保护

```
当前持仓:
- ETH 做多 4.87 个
- 入场价: $3,844
- 当前价: $3,880 (+0.9%)
- 止损: $3,715
- 止盈: $4,227

市场状态:
- RSI(7): 30.9 (仍然超卖)
- 价格未触及止损或止盈

AI 决策:
- 信号: HOLD (继续持有)
- 理由: 价格未触及退出条件，继续持有等待止盈
```

### 场景 3: 止损触发

```
当前持仓:
- XRP 做多 3542 个
- 入场价: $2.47
- 当前价: $2.41 (-2.4%)
- 止损: $2.34
- Invalidation: 价格跌破 $2.30

市场状态:
- 价格接近止损
- 下跌趋势持续

AI 决策:
- 信号: CLOSE (平仓)
- 理由: 价格接近失效条件，主动止损
```

## 风险提示

⚠️ **重要提示**:

1. 这是一个教育性项目，用于学习 AI 交易系统架构
2. 加密货币交易有极高风险，可能导致全部资金损失
3. 建议先在**测试网**充分测试
4. 使用真实资金前，请充分理解系统逻辑和风险
5. AI 模型的决策不代表任何投资建议
6. 高杠杆交易风险极大，请谨慎使用

## 调试技巧

### 1. 查看 AI Prompt
```bash
cat ai_trading/last_prompt.txt
```

### 2. 查看 AI 决策
```bash
cat ai_trading/last_decision.json | python -m json.tool
```

### 3. 测试单个模块
```python
# 测试技术指标计算
python ai_trading/market_data.py

# 测试 Prompt 构建
python ai_trading/prompt_builder.py
```

### 4. 只运行一次（测试模式）
```bash
python ai_trading/ai_trader_bot.py --test
```

## 常见问题

### Q: 如何获取 Anthropic API Key?
A: 访问 https://console.anthropic.com/ 注册并获取

### Q: 如何切换到主网?
A: 修改配置文件中的 `use_testnet` 为 `false`，并确保钱包有足够资金

### Q: 为什么 AI 不开仓?
A: 可能原因：
- 市场条件不满足
- 风险收益比不够
- 订单价值低于最小值
- 账户资金不足

### Q: 如何调整交易间隔?
A: 使用 `--interval` 参数，如 `--interval 5` (5分钟)

### Q: 可以添加其他币种吗?
A: 是的，使用 `--coins` 参数，如 `--coins BTC ETH SOL AVAX`

## 性能优化建议

1. **并行处理** - 可以并行获取多个币种的数据
2. **缓存** - 缓存技术指标计算结果
3. **WebSocket** - 使用 WebSocket 获取实时价格（更低延迟）
4. **数据库** - 存储历史交易数据，用于回测和分析

## 后续改进方向

- [ ] 添加回测系统
- [ ] 支持更多技术指标
- [ ] 多 AI 模型组合决策
- [ ] 风险管理优化
- [ ] 交易分析和报告生成
- [ ] Web 界面监控面板
- [ ] 支持其他交易所

## 参考资源

- [nof1.ai](https://nof1.ai/) - AI 交易竞赛平台
- [Hyperliquid 文档](https://hyperliquid.gitbook.io/)
- [Anthropic Claude 文档](https://docs.anthropic.com/)

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

