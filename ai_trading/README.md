# AI 交易机器人

基于 DeepSeek AI + Hyperliquid 的自动化交易系统。

---

## 快速开始

### 查看交易历史和 AI 推理过程

系统会自动保存每次交易的完整信息，包括 AI 的推理过程：

```bash
# 列出最近 10 次交易
python3 view_history.py list 10

# 查看某次交易的详细信息
python3 view_history.py show ai_trading/history/20251022_114938

# 查看 AI 的推理过程（仅 deepseek-reasoner 模型）
python3 view_history.py reasoning ai_trading/history/20251022_114938

# 查看 AI 的完整响应
python3 view_history.py response ai_trading/history/20251022_114938

# 查看 Token 使用统计
python3 view_history.py tokens
```

**历史记录包含的文件**：
- `reasoning.txt` - AI 的推理过程（deepseek-reasoner 模型专有）
- `response.txt` - AI 的完整响应
- `ai_response.json` - API 响应元数据（token 使用量等）
- `decision.json` - 解析后的交易决策
- `prompt.txt` - 发送给 AI 的 prompt
- `summary.json` - 交易周期摘要

详见：[HISTORY_FILES.md](HISTORY_FILES.md)

---

### 方式一：使用启动脚本（推荐）

```bash
# 1. 创建 .env 配置文件（使用 python-dotenv）
cd ai_trading
cp .env.example .env
nano .env  # 编辑并填入你的 API Key

# 2. 运行脚本
bash start_deepseek.sh

# 3. 仅测试一次（不循环）
bash start_deepseek.sh --test
```

**或者直接运行 Python**：
```bash
cd ai_trading
python3 ai_trader_bot.py --test  # 会自动从 .env 加载配置

# 交易市值前20名的币种（显示友好名称如BTC, ETH）
python3 ai_trader_bot.py --top-coins 20 --test

# 指定特定币种
python3 ai_trader_bot.py --coins BTC ETH SOL --test
```

**使用 python-dotenv 自动加载**:
- ✅ 自动从 `.env` 文件加载 API Key
- ✅ 支持任何运行方式（bash 脚本或直接 python）
- ✅ 符合 12-factor app 最佳实践
- ✅ 使用 deepseek-reasoner 模型
- ✅ 支持按市值排序选择前N个币种（`--top-coins N`，显示友好名称）
- ✅ 支持指定特定币种交易（`--coins BTC ETH SOL`）
- ✅ 在测试网运行

### 方式二：手动运行

```bash
# 1. 设置 API Key
export DEEPSEEK_API_KEY='your-api-key'

# 2. 运行（测试模式）
python3 ai_trader_bot.py --test

# 3. 实盘运行（每3分钟交易一次）
python3 ai_trader_bot.py --interval 3
```

---

## 系统架构

```
市场数据 → AI 分析 → 交易执行 → 历史记录
   ↓          ↓         ↓           ↓
K线/指标   DeepSeek   Hyperliquid  自动存储
```

**核心组件**:
- `ai_trader_bot.py` - 主程序
- `market_data.py` - 市场数据和技术指标
- `prompt_builder.py` - AI Prompt 构建
- `order_executor.py` - 订单执行

---

## 主要功能

### 1. 技术指标
- **EMA(20)**: 趋势跟踪
- **MACD**: 动量指标
- **RSI(7/14)**: 超买超卖
- **ATR**: 波动率
- **成交量**: 市场活跃度

### 2. RSI 背离检测 ⚠️

**背离是 RSI 最强的反转信号**

| 类型 | 特征 | 信号 |
|------|-----|------|
| 顶背离 | 价格 ↑ RSI ↓ | 📉 看跌 |
| 底背离 | 价格 ↓ RSI ↑ | 📈 看涨 |

**强度分级**:
- **Strong**: RSI 差异 > 10 点
- **Moderate**: RSI 差异 5-10 点
- **Weak**: RSI 差异 < 5 点

**多周期确认**: RSI(7) + RSI(14) 同时背离 = 🔥 超强信号

### 3. 交易决策

AI 每次可以选择：
- **ENTRY**: 开仓（做多/做空）
- **HOLD**: 保持当前状态
- **CLOSE**: 平仓

**风控**:
- 杠杆: 5x-40x
- 自动止损/止盈
- 最小订单金额: $10

---

## 历史记录系统

```
ai_trading/history/
├── 20251022_143052/        # 每个交易周期一个文件夹
│   ├── prompt.txt          # 发给 AI 的完整 prompt
│   ├── decision.json       # AI 的交易决策
│   └── summary.json        # 账户状态摘要
└── ...（自动保留最新50个）
```

**查看历史**:
```bash
# 列出所有交易记录
python3 view_history.py --list

# 查看最新一次
python3 view_history.py --latest
```

**快速访问**:
- `last_prompt.txt` - 最新的 prompt
- `last_decision.json` - 最新的决策

---

## 配置参数

### 修改启动脚本

编辑 `start_deepseek.sh`（第22-27行）：

```bash
python ai_trading/ai_trader_bot.py \
    --model deepseek-reasoner \     # 更换模型
    --coins BTC ETH SOL \           # 修改币种
    --interval 3 \                  # 调整间隔
    --testnet \                     # 删除此行用主网
    "$@"
```

### 命令行参数

```bash
python3 ai_trader_bot.py \
  --coins BTC ETH SOL \      # 交易币种
  --interval 3 \             # 间隔（分钟）
  --testnet \                # 使用测试网
  --model deepseek-reasoner  # AI 模型
```

**模型选择**:
- `deepseek-reasoner`: 推理能力强（推荐）
- `deepseek-chat`: 速度快

---

## Prompt 示例

AI 看到的信息包括：

```
ALL BTC DATA
current_price = 108114, current_rsi (7) = 29.3

BTC mid prices: [107979, 108000, ..., 107798]
RSI(14): [61.14, 61.54, ..., 44.07]

======================================================================
⚠️ RSI 背离信号检测 - 强力反转信号
======================================================================
背离是RSI指标中威力最强的信号，往往预示着潜在的趋势反转。

[信号 1] RSI(14) - 顶背离 (看跌)
  强度: 强
  详情: 价格从 108000 上涨至 108114，但 RSI 从 65.3 下降至 44.1
  📉 建议: 考虑做空或平掉多仓

🔥 多周期确认: RSI(7) 和 RSI(14) 同时出现背离，信号更强！
======================================================================

HERE IS YOUR ACCOUNT INFORMATION
Total Return: +5.23%
Available Cash: $4927.64
Current Account Value: $11187.63
```

---

## 实战建议

### 初次使用
1. **使用启动脚本** - 运行 `bash start_deepseek.sh --test` 测试一次
2. **先用测试网** - 脚本默认使用测试网（`--testnet`）
3. **小金额测试** - 初始 $100-$500
4. **观察几天** - 再增加资金

### 参数调整
- **保守**: `--interval 15` (15分钟一次)
- **积极**: `--interval 3` (3分钟一次)
- **币种**: 选择流动性好的主流币

### 风险管理
- ✅ 定期检查账户状态
- ✅ 设置总资金上限
- ✅ 监控 Sharpe Ratio
- ⚠️ 异常波动时暂停

---

## 技术细节

### RSI 背离检测算法

```python
# 1. 找到价格和RSI的局部高低点
price_peaks, price_troughs = find_peaks_and_troughs(prices)
rsi_peaks, rsi_troughs = find_peaks_and_troughs(rsi_values)

# 2. 判断背离
if price ↑ and rsi ↓:
    → 顶背离（看跌）
if price ↓ and rsi ↑:
    → 底背离（看涨）

# 3. 计算强度
rsi_diff = abs(rsi_peak1 - rsi_peak2)
```

### 数据流

```
Hyperliquid API (K线数据)
    ↓
MarketDataFetcher.get_market_state()
    ↓ (计算指标 + 检测背离)
PromptBuilder.build_prompt()
    ↓ (构建 AI 输入)
DeepSeek API
    ↓ (AI 决策)
OrderExecutor.execute_decision()
    ↓ (执行交易)
History (自动保存)
```

---

## 文件说明

| 文件 | 用途 |
|------|------|
| `ai_trader_bot.py` | 主程序入口（使用 python-dotenv 自动加载配置） |
| `market_data.py` | 市场数据 + 技术指标 + 背离检测 |
| `prompt_builder.py` | AI Prompt 生成 |
| `order_executor.py` | 订单执行和管理 |
| `view_history.py` | 历史记录查看工具 |
| `start_deepseek.sh` | 一键启动脚本 |
| `.env.example` | 环境变量模板（复制为 .env 使用） |
| `.env` | API Key 配置（不提交到 Git，使用 python-dotenv 加载） |

---

## 常见问题

**Q: 初始资金从哪里来？**  
A: 自动从你的 Hyperliquid 账户读取实际余额

**Q: 如何停止机器人？**  
A: 按 `Ctrl+C`

**Q: 背离信号准确率多少？**  
A: 需要实盘验证，理论上强背离 65-75%，多周期确认 75-85%

**Q: 支持哪些币种？**  
A: Hyperliquid 支持的所有永续合约（BTC, ETH, SOL, BNB, DOGE, XRP 等）

**Q: 最小资金要求？**  
A: 建议至少 $100（测试网免费）

---

## 更新日志

### v1.2 (2025-10-22)
- ✅ 新增 RSI 背离检测（P0/P1/P2）
- ✅ 多周期背离确认
- ✅ 背离强度分级
- ✅ 自动读取实际账户余额
- ✅ 修复 `market_open()` 参数错误
- ✅ DeepSeek max_tokens 优化

### v1.1
- ✅ 历史记录系统
- ✅ 自动清理旧记录（保留50个）

### v1.0
- ✅ 基础交易功能
- ✅ 技术指标计算
- ✅ DeepSeek AI 集成

---

**License**: MIT  
**Status**: ✅ Production Ready  
**Last Updated**: 2025-10-22
