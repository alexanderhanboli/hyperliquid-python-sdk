# AI 交易机器人使用指南

## 🎯 项目概述

这是一个完整复现 [nof1.ai](https://nof1.ai/) 架构的 AI 交易系统，使用 **Claude Sonnet 4.5** 作为交易决策引擎。

### 核心特性

✅ **自动数据收集** - 每 3 分钟自动获取市场数据和技术指标  
✅ **AI 驱动决策** - 使用 Claude 分析市场并生成交易信号  
✅ **自动风险管理** - 每笔交易自动设置止盈止损  
✅ **支持多币种** - 可同时交易 BTC, ETH, SOL, BNB, XRP, DOGE 等  
✅ **测试网支持** - 在测试网安全练习，不使用真实资金  

## 📁 文件结构

```
ai_trading/
├── market_data.py          # 市场数据获取和技术指标计算
├── prompt_builder.py       # AI Prompt 构建器
├── order_executor.py       # 订单执行器
├── ai_trader_bot.py        # 主程序（⭐ 启动入口）
├── test_system.py          # 系统测试脚本
├── quick_start.sh          # 快速启动脚本（Shell）
├── config.json.example     # 配置文件示例
└── README.md               # 详细文档
```

## 🚀 快速开始

### 第 1 步：安装依赖

```bash
# 激活虚拟环境（如果有）
source venv/bin/activate

# 安装必要的包
pip install numpy pandas anthropic schedule
```

### 第 2 步：设置 Anthropic API Key

获取 API Key：访问 https://console.anthropic.com/

```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

或者在 `.bashrc` / `.zshrc` 中永久设置：
```bash
echo 'export ANTHROPIC_API_KEY="your-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

### 第 3 步：测试系统

```bash
# 运行系统测试，确保一切正常
python ai_trading/test_system.py
```

应该看到所有测试都通过 ✅

### 第 4 步：测试运行（只运行一次）

```bash
# 测试模式：只执行一次交易循环
python ai_trading/ai_trader_bot.py --test
```

### 第 5 步：启动机器人（正常模式）

```bash
# 每 3 分钟自动运行一次
python ai_trading/ai_trader_bot.py

# 或者自定义币种和间隔
python ai_trading/ai_trader_bot.py --coins BTC ETH SOL --interval 5
```

## 📊 系统工作流程

```
[每 3 分钟]
    ↓
1. 获取市场数据
   - 获取价格、K线
   - 计算 EMA, MACD, RSI, ATR
    ↓
2. 构建 AI Prompt
   - 格式化市场数据
   - 包含账户状态
    ↓
3. 调用 Claude API
   - 分析市场数据
   - 返回交易决策 (JSON)
    ↓
4. 执行交易
   - 开仓/平仓/持仓
   - 自动设置止盈止损
    ↓
5. 记录结果
   - 保存 prompt 和决策
   - 更新账户状态
```

## 💡 AI 决策示例

### 开仓信号

当 AI 检测到市场机会时，会返回：

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
      "leverage": 10,
      "confidence": 0.75,
      "justification": "RSI 超卖在 29，MACD 显示看涨背离..."
    }
  }
}
```

机器人会：
1. 以 10x 杠杆开多仓 0.1 BTC
2. 设置止盈在 $110,000
3. 设置止损在 $105,000

### 持仓信号

当条件未触发时，AI 会返回 `"signal": "hold"`，保持当前仓位。

### 平仓信号

当失效条件触发时，AI 会返回 `"signal": "close"`，平掉仓位。

## 🛠️ 命令行参数

```bash
python ai_trading/ai_trader_bot.py [选项]

选项:
  --coins COIN1 COIN2 ...   交易的币种列表 (默认: BTC ETH SOL)
  --interval N              交易间隔，单位：分钟 (默认: 3)
  --testnet                 使用测试网 (默认: True)
  --test                    测试模式，只运行一次
  --api-key KEY             Anthropic API Key (或使用环境变量)

示例:
  # 只交易 BTC 和 ETH，每 5 分钟一次
  python ai_trading/ai_trader_bot.py --coins BTC ETH --interval 5
  
  # 测试模式
  python ai_trading/ai_trader_bot.py --test
```

## 📈 查看运行结果

### 查看最新的 AI Prompt
```bash
cat ai_trading/last_prompt.txt
```

### 查看最新的 AI 决策
```bash
cat ai_trading/last_decision.json
```

### 实时监控
机器人运行时会在终端显示：
- 当前价格和技术指标
- 账户价值和收益率
- 持仓情况
- AI 决策和执行结果

## ⚙️ 配置说明

可以创建 `ai_trading/config.json` 自定义配置：

```json
{
  "coins": ["BTC", "ETH", "SOL"],
  "interval_minutes": 3,
  "use_testnet": true,
  "initial_capital": 10000.0,
  "leverage": {
    "default": 10,
    "max": 40,
    "min": 5
  },
  "trading_rules": {
    "no_pyramiding": true,
    "always_use_stop_loss": true,
    "min_order_value_usd": 10.0
  }
}
```

## 🔍 技术指标说明

机器人会计算以下指标供 AI 分析：

| 指标 | 说明 | 用途 |
|------|------|------|
| **EMA20** | 20期指数移动平均 | 判断短期趋势 |
| **MACD** | 指数平滑异同移动平均线 | 找趋势转折点 |
| **RSI(7)** | 7期相对强弱指标 | 超买/超卖（更敏感） |
| **RSI(14)** | 14期相对强弱指标 | 超买/超卖（标准） |
| **ATR** | 平均真实波幅 | 衡量波动性 |

RSI 解读：
- RSI < 30：超卖（可能反弹）
- RSI > 70：超买（可能回调）

## 📚 从 nof1.ai 学到的架构

### 1. **结构化的市场数据输入**
nof1.ai 为 AI 提供：
- 当前价格和技术指标
- 最近 10 个数据点的序列（价格、EMA、MACD、RSI）
- 4 小时时间框架的长期趋势
- 持仓量和资金费率

我们完全复现了这个数据结构。

### 2. **严格的 JSON 输出格式**
AI 必须返回结构化的 JSON，包含：
- 明确的信号类型（entry/hold/close）
- 具体的数值（数量、止盈、止损、杠杆）
- 风险管理参数（confidence、risk_usd）
- 决策理由（justification）

### 3. **交易规则约束**
- 不允许加仓（No pyramiding）
- 必须设置止盈止损
- 风险收益比至少 1:2
- 杠杆限制在 5x-40x

### 4. **完整的反馈循环**
每次决策后，下次 prompt 会包含：
- 上次决策的结果
- 当前持仓状态
- 账户盈亏情况

这让 AI 能够"学习"和调整策略。

## 🧪 调试技巧

### 1. 单独测试各个模块

```bash
# 测试技术指标计算
python ai_trading/market_data.py

# 测试 Prompt 构建
python ai_trading/prompt_builder.py
```

### 2. 检查 API 调用

如果 AI 决策异常，检查 `last_prompt.txt` 确认数据是否正确。

### 3. 模拟 AI 响应

可以手动编辑 `last_decision.json` 然后注释掉 AI 调用，测试订单执行逻辑。

## ⚠️ 风险提示

### 重要警告

1. **这是教育项目** - 主要用于学习 AI 交易系统架构
2. **加密货币风险极高** - 可能损失全部资金
3. **先用测试网** - 充分测试后再考虑真实交易
4. **高杠杆危险** - 40x 杠杆可以快速爆仓
5. **AI 不保证盈利** - AI 的决策不是投资建议

### 建议

- ✅ 在测试网运行至少 1-2 周
- ✅ 从低杠杆开始（5x-10x）
- ✅ 只用可以承受损失的资金
- ✅ 定期监控机器人状态
- ✅ 设置账户总风险限制

## 🐛 常见问题

### Q: AI 不开仓怎么办？
**A:** 可能原因：
- 市场条件不满足（RSI、MACD 等指标）
- 风险收益比不够好
- 订单价值低于最小值（默认 $10）
- 账户余额不足

查看 `last_prompt.txt` 和 `last_decision.json` 了解 AI 的思考过程。

### Q: 如何切换到主网？
**A:** 
1. 确保充分理解风险
2. 在主程序中设置 `use_testnet=False`
3. 确保钱包有足够资金

### Q: 可以 24/7 运行吗？
**A:** 可以，但建议：
- 使用云服务器或一直开着的电脑
- 设置日志和监控
- 定期检查机器人状态
- 设置最大损失限制

### Q: 如何停止机器人？
**A:** 按 `Ctrl+C` 停止。机器人会显示交易总结。

### Q: 可以添加其他币种吗？
**A:** 可以，只要 Hyperliquid 支持：
```bash
python ai_trading/ai_trader_bot.py --coins BTC ETH SOL AVAX MATIC
```

## 🔗 相关资源

- [nof1.ai](https://nof1.ai/) - AI 交易竞赛平台
- [Hyperliquid 文档](https://hyperliquid.gitbook.io/)
- [Anthropic Claude](https://www.anthropic.com/claude)
- [本项目 README](ai_trading/README.md)

## 📞 获取帮助

如果遇到问题：
1. 先运行 `python ai_trading/test_system.py` 检查系统
2. 查看 `last_prompt.txt` 和 `last_decision.json`
3. 查看终端输出的错误信息
4. 检查 API Key 是否正确设置

## 🎓 学习建议

### 对于初学者
1. 先阅读 `ORDER_TYPES_GUIDE.md` 了解订单类型
2. 运行 `order_practice.py` 练习手动下单
3. 理解技术指标（EMA、MACD、RSI）
4. 在测试网运行机器人 1-2 周
5. 分析 AI 的决策逻辑

### 对于开发者
1. 研究 `market_data.py` 了解数据获取
2. 研究 `prompt_builder.py` 了解如何设计 AI prompt
3. 研究 `order_executor.py` 了解订单执行
4. 尝试添加新的技术指标
5. 尝试改进 prompt 结构

### 对于交易者
1. 理解机器人的交易逻辑
2. 监控 AI 的决策质量
3. 调整风险参数（杠杆、止损等）
4. 记录和分析交易结果
5. 根据回测优化策略

## 🚧 未来改进方向

- [ ] 添加回测系统
- [ ] 支持更多技术指标（布林带、斐波那契等）
- [ ] 多 AI 模型组合决策（Claude + GPT-4 + Gemini）
- [ ] Web 界面监控面板
- [ ] 交易报告生成
- [ ] 风险预警系统
- [ ] 支持其他交易所

## 📜 许可证

MIT License - 自由使用，但需承担风险

---

**祝交易顺利！记住：风险管理永远是第一位的！** 🚀

