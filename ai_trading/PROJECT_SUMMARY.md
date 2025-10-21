# AI 交易机器人项目总结

## 📦 项目概述

这是一个完整复现 [nof1.ai](https://nof1.ai/) 架构的 AI 自动交易系统。

**核心特性:**
- 🤖 使用 Claude Sonnet 4.5 作为决策引擎
- 📊 自动获取市场数据并计算技术指标
- ⚡ 自动执行交易，设置止盈止损
- 🔄 每 3 分钟运行一次交易循环
- 🛡️ 完整的风险管理机制

## 📂 项目结构

```
hyperliquid-python-sdk/
├── ai_trading/                        # ⭐ AI 交易系统目录
│   ├── __init__.py                    # Python 包初始化
│   ├── market_data.py                 # 市场数据获取和技术指标计算
│   ├── prompt_builder.py              # AI Prompt 构建器
│   ├── order_executor.py              # 订单执行器
│   ├── ai_trader_bot.py               # ⭐ 主程序（启动入口）
│   ├── test_system.py                 # 系统测试脚本
│   ├── quick_start.sh                 # Shell 快速启动脚本
│   ├── config.json.example            # 配置文件示例
│   ├── README.md                      # 详细系统说明
│   └── PROJECT_SUMMARY.md             # 本文件
│
├── ai_trading_demo.py                 # 🎬 交互式演示脚本
├── AI_TRADING_GUIDE.md                # 📖 完整使用指南
│
├── order_practice.py                  # 订单类型练习脚本
├── ORDER_TYPES_GUIDE.md               # 订单类型详解
├── ORDER_QUICK_REFERENCE.md           # 订单快速参考
├── QUICK_START.md                     # 快速开始指南
│
├── hyperliquid/                       # Hyperliquid SDK
│   ├── info.py                        # Info API
│   ├── exchange.py                    # Exchange API
│   └── ...
│
└── examples/                          # 示例代码
    ├── config.json                    # Hyperliquid 配置
    ├── example_utils.py               # 工具函数
    └── ...
```

## 🔧 核心模块说明

### 1. market_data.py - 市场数据模块

**功能:**
- 获取实时价格
- 获取 K 线数据（多种时间周期）
- 计算技术指标

**关键类:**
- `TechnicalIndicators` - 技术指标计算
  - `calculate_ema()` - 指数移动平均
  - `calculate_macd()` - MACD 指标
  - `calculate_rsi()` - RSI 指标
  - `calculate_atr()` - ATR 波动率

- `MarketDataFetcher` - 数据获取器
  - `get_current_prices()` - 获取当前价格
  - `get_candles()` - 获取 K 线数据
  - `get_market_state()` - 获取完整市场状态

**技术指标:**
| 指标 | 周期 | 说明 |
|------|------|------|
| EMA | 20, 50 | 趋势判断 |
| MACD | 12, 26, 9 | 趋势转折 |
| RSI | 7, 14 | 超买超卖 |
| ATR | 3, 14 | 波动率 |

### 2. prompt_builder.py - Prompt 构建器

**功能:**
- 将市场数据格式化为 AI 可理解的 prompt
- 包含完整的技术指标序列
- 添加账户状态和持仓信息
- 提供交易规则和指令

**输出格式:**
```
USER_PROMPT
It has been X minutes since you started trading...

CURRENT MARKET STATE FOR ALL COINS
ALL BTC DATA
current_price = ..., current_ema20 = ..., ...

Intraday series (3-minute intervals):
Mid prices: [...]
EMA indicators: [...]
...

HERE IS YOUR ACCOUNT INFORMATION & PERFORMANCE
Current Total Return: X%
Available Cash: $X
...

INSTRUCTIONS:
Based on the market data above, make your trading decisions...
```

### 3. order_executor.py - 订单执行器

**功能:**
- 解析 AI 决策
- 执行开仓/平仓
- 设置止盈止损
- 管理持仓

**核心方法:**
- `execute_decision()` - 执行 AI 决策
- `_execute_entry()` - 执行开仓
- `_execute_hold()` - 保持持仓
- `_execute_close()` - 执行平仓
- `_set_stop_loss()` - 设置止损
- `_set_take_profit()` - 设置止盈
- `get_current_positions()` - 获取当前持仓
- `get_account_value()` - 获取账户价值

**安全机制:**
- 最小订单价值检查（默认 $10）
- 止损止盈自动设置
- 仓位管理（不允许加仓）
- 错误处理和日志记录

### 4. ai_trader_bot.py - 主程序 ⭐

**功能:**
- 定时执行交易循环
- 调用 Claude API
- 协调各个模块
- 记录交易结果

**工作流程:**
```
[启动] → [初始化API] → [定时器: 每N分钟]
             ↓
    ┌────────────────────┐
    │  1. 获取市场数据    │
    │  2. 构建 AI Prompt │
    │  3. 调用 Claude API │
    │  4. 执行交易决策    │
    │  5. 记录结果        │
    └────────────────────┘
             ↓
    [继续循环] or [Ctrl+C 停止]
```

**命令行参数:**
```bash
python ai_trading/ai_trader_bot.py [选项]

--coins COIN1 COIN2     # 交易币种
--interval N            # 交易间隔（分钟）
--testnet              # 使用测试网
--test                 # 测试模式（只运行一次）
--api-key KEY          # Anthropic API Key
```

## 🎯 AI 决策格式

AI (Claude) 需要返回 JSON 格式的决策：

### 开仓决策
```json
{
  "BTC": {
    "trade_signal_args": {
      "coin": "BTC",
      "signal": "entry",
      "is_buy": true,
      "quantity": 0.1,
      "profit_target": 115000,
      "stop_loss": 105000,
      "invalidation_condition": "If price closes below 105000",
      "leverage": 10,
      "confidence": 0.75,
      "risk_usd": 500,
      "justification": "RSI oversold, MACD bullish divergence..."
    }
  }
}
```

### 持仓决策
```json
{
  "BTC": {
    "trade_signal_args": {
      "coin": "BTC",
      "signal": "hold",
      "quantity": 0.1,
      ...
    }
  }
}
```

### 平仓决策
```json
{
  "BTC": {
    "trade_signal_args": {
      "coin": "BTC",
      "signal": "close",
      "quantity": 0.1,
      "justification": "Invalidation condition met"
    }
  }
}
```

## 📊 数据流

```
Hyperliquid Exchange
        ↓
   [价格数据]
        ↓
MarketDataFetcher
   - 获取 K 线
   - 计算指标
        ↓
  [技术指标]
        ↓
PromptBuilder
   - 格式化数据
   - 添加账户信息
        ↓
  [AI Prompt]
        ↓
Claude Sonnet 4.5
   - 分析市场
   - 生成决策
        ↓
  [JSON 决策]
        ↓
OrderExecutor
   - 执行订单
   - 设置止盈止损
        ↓
Hyperliquid Exchange
```

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install numpy pandas anthropic schedule
```

### 2. 设置 API Key
```bash
export ANTHROPIC_API_KEY='your-api-key'
```

### 3. 运行测试
```bash
python ai_trading/test_system.py
```

### 4. 运行演示
```bash
python ai_trading_demo.py
```

### 5. 启动机器人
```bash
# 测试模式
python ai_trading/ai_trader_bot.py --test

# 正常模式
python ai_trading/ai_trader_bot.py
```

## 📖 文档索引

| 文档 | 内容 | 读者 |
|------|------|------|
| `AI_TRADING_GUIDE.md` | 完整使用指南 | 所有用户 ⭐ |
| `ai_trading/README.md` | 系统架构说明 | 开发者 |
| `PROJECT_SUMMARY.md` | 项目总结（本文件） | 快速了解 |
| `ORDER_TYPES_GUIDE.md` | 订单类型详解 | 初学者 |
| `QUICK_START.md` | SDK 快速开始 | SDK 用户 |

## 🧪 测试和调试

### 系统测试
```bash
python ai_trading/test_system.py
```

测试内容:
- ✅ 模块导入
- ✅ Hyperliquid 连接
- ✅ 市场数据获取
- ✅ K 线数据和指标计算
- ✅ Prompt 构建
- ✅ Anthropic API 连接

### 调试文件
- `ai_trading/last_prompt.txt` - 最后的 AI prompt
- `ai_trading/last_decision.json` - 最后的 AI 决策
- `ai_trading/demo_prompt.txt` - 演示的 prompt

### 查看日志
机器人运行时会在终端显示详细日志：
- 市场数据获取
- AI 决策内容
- 订单执行结果
- 账户状态更新

## 🎓 学习路径

### 初学者
1. 阅读 `AI_TRADING_GUIDE.md`
2. 运行 `python ai_trading_demo.py` 了解流程
3. 阅读 `ORDER_TYPES_GUIDE.md` 学习订单
4. 运行 `python order_practice.py` 练习下单
5. 在测试网运行机器人 1-2 周

### 开发者
1. 研究 `market_data.py` 的数据获取逻辑
2. 研究 `prompt_builder.py` 的 prompt 设计
3. 研究 `order_executor.py` 的订单执行
4. 尝试添加新的技术指标
5. 优化 AI prompt 结构

### 交易者
1. 理解技术指标的含义
2. 分析 AI 的决策逻辑
3. 监控交易表现
4. 调整风险参数
5. 优化交易策略

## 🔐 安全建议

### 测试网先行
- ✅ 在测试网运行至少 1-2 周
- ✅ 验证所有功能正常
- ✅ 理解 AI 决策逻辑
- ✅ 建立风险管理经验

### 风险管理
- ✅ 只用可承受损失的资金
- ✅ 从低杠杆开始（5x-10x）
- ✅ 设置最大损失限制
- ✅ 定期监控机器人状态
- ✅ 记录和分析交易结果

### API 密钥安全
- ✅ 不要提交 API Key 到 Git
- ✅ 使用环境变量存储
- ✅ 定期更换密钥
- ✅ 限制 API 权限

## 🐛 常见问题

### Q: K 线数据获取失败？
**A:** 检查：
- 网络连接
- Hyperliquid API 是否正常
- 币种名称是否正确

### Q: AI 决策格式错误？
**A:** 查看 `last_decision.json`，确认 JSON 格式正确

### Q: 订单执行失败？
**A:** 可能原因：
- 账户余额不足
- 订单价值低于最小值
- 网络问题

### Q: 如何停止机器人？
**A:** 按 `Ctrl+C`，机器人会显示交易总结

## 📊 性能指标

机器人会追踪以下指标：
- **总收益率** - (当前价值 - 初始资金) / 初始资金
- **Sharpe Ratio** - 风险调整后收益
- **交易次数** - 执行的交易数量
- **胜率** - 盈利交易占比
- **最大回撤** - 最大损失百分比

## 🔮 未来改进

- [ ] 回测系统
- [ ] 更多技术指标（布林带、斐波那契等）
- [ ] 多 AI 模型组合
- [ ] Web 监控面板
- [ ] 自动报告生成
- [ ] 风险预警系统
- [ ] 支持更多交易所

## 📞 获取帮助

遇到问题？
1. 运行 `python ai_trading/test_system.py` 检查系统
2. 查看 `last_prompt.txt` 和 `last_decision.json`
3. 检查终端错误信息
4. 阅读相关文档

## 🙏 致谢

- [nof1.ai](https://nof1.ai/) - 提供了优秀的架构设计
- [Hyperliquid](https://hyperliquid.xyz/) - 提供了强大的交易 API
- [Anthropic](https://www.anthropic.com/) - Claude AI 模型

## 📜 许可证

MIT License

---

**项目完成日期:** 2025-10-21  
**版本:** v1.0.0  
**状态:** ✅ 生产就绪（测试网）

祝交易顺利！🚀

