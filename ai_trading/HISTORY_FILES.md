# 交易历史记录文件说明

每次交易循环都会在 `ai_trading/history/` 目录下创建一个独立的文件夹，文件夹名格式为 `YYYYMMDD_HHMMSS`。

## 文件结构

每个交易周期文件夹包含以下文件：

### 📝 输入文件

- **`prompt.txt`** - 发送给 AI 的完整 prompt
  - 包含市场数据、账户信息、持仓情况
  - 包含交易指令和规则
  - 用于审查 AI 收到的信息是否正确

### 🤖 AI 响应文件

- **`response.txt`** - AI 返回的完整响应内容
  - 纯文本格式，易于阅读
  - 包含 AI 的最终输出（通常是 JSON 格式的决策）

- **`reasoning.txt`** - AI 的推理过程（仅 deepseek-reasoner 模型）
  - DeepSeek Reasoner 模型特有
  - 详细记录 AI 的思考过程和分析逻辑
  - 对于理解 AI 决策非常有价值

- **`ai_response.json`** - API 响应的元数据
  ```json
  {
    "model": "deepseek-reasoner",
    "created": 1729580378,
    "finish_reason": "stop",
    "has_reasoning": true,
    "reasoning_length": 12543,
    "response_length": 856,
    "usage": {
      "prompt_tokens": 5234,
      "completion_tokens": 892,
      "total_tokens": 6126
    }
  }
  ```

### 📊 决策和摘要文件

- **`decision.json`** - AI 的交易决策（解析后的 JSON）
  ```json
  {
    "BTC": {
      "trade_signal_args": {
        "coin": "BTC",
        "signal": "entry",
        "is_buy": true,
        "quantity": 0.01,
        "profit_target": 105000,
        "stop_loss": 95000,
        ...
      }
    }
  }
  ```

- **`summary.json`** - 交易周期摘要
  ```json
  {
    "timestamp": "2025-10-22 11:49:41",
    "invocation_count": 27,
    "account_value": 946.35,
    "available_cash": 916.45,
    "return_pct": -4.40,
    "sharpe_ratio": -2.46,
    "positions_count": 1
  }
  ```

## 文件用途

### 调试和分析

1. **查看 AI 的思考过程**
   ```bash
   cat ai_trading/history/20251022_114938/reasoning.txt
   ```

2. **检查 AI 的完整响应**
   ```bash
   cat ai_trading/history/20251022_114938/response.txt
   ```

3. **查看 token 使用情况**
   ```bash
   cat ai_trading/history/20251022_114938/ai_response.json | jq .usage
   ```

### 性能优化

- 通过 `ai_response.json` 监控 token 使用量
- 对于 deepseek-reasoner，reasoning_length 显示推理过程的长度
- 可以分析哪些 prompt 导致了过长的 token 消耗

### 策略回测

- `prompt.txt` + `decision.json` 可以用于回放决策过程
- `reasoning.txt` 可以帮助理解 AI 的决策逻辑
- 结合 `summary.json` 分析决策效果

## 历史记录管理

- 系统自动保留最近 **50 个**交易周期
- 超过 50 个时，自动删除最旧的记录
- 可在 `ai_trader_bot.py` 中修改保留数量

## 快速访问文件

以下文件保存在 `ai_trading/` 根目录，始终是最新一次交易的结果：

- `last_prompt.txt` - 最新的 prompt
- `last_decision.json` - 最新的决策

## 示例：查看最近一次 AI 推理

```bash
# 查看最新的交易周期文件夹
ls -lt ai_trading/history/ | head -n 2

# 查看 reasoning（如果存在）
cat ai_trading/history/$(ls -t ai_trading/history/ | head -n 1)/reasoning.txt

# 查看 token 使用统计
find ai_trading/history -name "ai_response.json" -exec jq '.usage.total_tokens' {} \; | \
  awk '{sum+=$1; count++} END {print "平均 tokens:", sum/count, "总计:", sum}'
```

## 注意事项

1. **reasoning.txt 只在使用 deepseek-reasoner 模型时生成**
   - deepseek-chat 模型不会生成此文件
   
2. **文件编码**
   - 所有文本文件使用 UTF-8 编码
   - JSON 文件使用 `ensure_ascii=False` 以正确显示中文

3. **磁盘空间**
   - 每个交易周期约占用 20-200KB（取决于 reasoning 长度）
   - 50 个周期约占 1-10MB 空间

