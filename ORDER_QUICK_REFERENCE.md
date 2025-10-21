# 📋 订单类型快速参考卡片

## 🔍 快速查找

| 想要做什么 | 使用什么 | 跳转到 |
|-----------|---------|--------|
| 指定价格买卖 | 限价单 | [→](#限价单) |
| 立即成交 | 市价单 | [→](#市价单) |
| 自动止损 | 止损单 | [→](#止损单) |
| 自动止盈 | 止盈单 | [→](#止盈单) |

---

## 限价单

**用途**: 指定价格买卖，价格可控

```python
exchange.order(
    name="ETH",              # 币种
    is_buy=True,             # True=买, False=卖
    sz=0.1,                  # 数量
    limit_px=3000.0,         # 限价
    order_type={"limit": {"tif": "Gtc"}},  # GTC/IoC/Alo
    reduce_only=False        # 是否只减仓
)
```

**TIF 选项**:
- `"Gtc"` - 一直有效直到取消（最常用）
- `"Ioc"` - 立即成交或取消
- `"Alo"` - 只做市商（不立即成交）

---

## 市价单

**用途**: 立即以当前价格成交

```python
# 市价买入
exchange.market_open(
    coin="ETH",
    is_buy=True,
    sz=0.1,
    slippage=0.05  # 5% 滑点容忍
)

# 市价平仓
exchange.market_close(coin="ETH")
```

---

## 止损单

**用途**: 价格达到止损价时自动平仓，保护资金

### 做多止损（买入后设置）

```python
exchange.order(
    name="ETH",
    is_buy=False,            # 止损是卖出
    sz=0.1,
    limit_px=2800.0,         # 低于触发价
    order_type={
        "trigger": {
            "triggerPx": 2900.0,   # 触发价
            "isMarket": True,       # 市价成交
            "tpsl": "sl"           # 标记为止损
        }
    },
    reduce_only=True         # ⚠️ 必须为 True
)
```

### 做空止损（卖出后设置）

```python
exchange.order(
    name="ETH",
    is_buy=True,             # 止损是买入
    sz=0.1,
    limit_px=3200.0,         # 高于触发价
    order_type={
        "trigger": {
            "triggerPx": 3100.0,
            "isMarket": True,
            "tpsl": "sl"
        }
    },
    reduce_only=True
)
```

---

## 止盈单

**用途**: 价格达到目标时自动平仓，锁定利润

### 做多止盈

```python
exchange.order(
    name="ETH",
    is_buy=False,            # 止盈是卖出
    sz=0.1,
    limit_px=3600.0,         # 高于触发价
    order_type={
        "trigger": {
            "triggerPx": 3500.0,   # 触发价
            "isMarket": True,
            "tpsl": "tp"           # 标记为止盈
        }
    },
    reduce_only=True
)
```

### 做空止盈

```python
exchange.order(
    name="ETH",
    is_buy=True,             # 止盈是买入
    sz=0.1,
    limit_px=2400.0,         # 低于触发价
    order_type={
        "trigger": {
            "triggerPx": 2500.0,
            "isMarket": True,
            "tpsl": "tp"
        }
    },
    reduce_only=True
)
```

---

## 📊 参数速查表

### exchange.order() 参数

| 参数 | 类型 | 说明 | 常用值 |
|------|------|------|--------|
| `name` | str | 币种 | "ETH", "BTC" |
| `is_buy` | bool | 买/卖 | True(买), False(卖) |
| `sz` | float | 数量 | 0.1, 1.0 |
| `limit_px` | float | 限价 | 3000.0 |
| `order_type` | dict | 订单类型 | 见下表 |
| `reduce_only` | bool | 只减仓 | True(止损止盈), False(开仓) |

### order_type 选项

#### 限价单
```python
{"limit": {"tif": "Gtc"}}  # 一直有效
{"limit": {"tif": "Ioc"}}  # 立即成交或取消
{"limit": {"tif": "Alo"}}  # 只做市商
```

#### 止损/止盈
```python
{
    "trigger": {
        "triggerPx": 3000.0,    # 触发价格
        "isMarket": True,        # 是否市价
        "tpsl": "sl"            # "sl"=止损, "tp"=止盈
    }
}
```

---

## 🎯 常见场景

### 场景 1: 低价买入

```python
# 当前价 $3500，想 $3000 买入
exchange.order("ETH", True, 0.1, 3000, {"limit": {"tif": "Gtc"}})
```

### 场景 2: 立即买入

```python
# 现在就要买
exchange.market_open("ETH", True, 0.1)
```

### 场景 3: 开多仓 + 止损止盈

```python
# 1. 买入开多
exchange.market_open("ETH", True, 0.1)

# 2. 设置 -5% 止损
stop_price = entry_price * 0.95
exchange.order("ETH", False, 0.1, stop_price*0.98, 
    {"trigger": {"triggerPx": stop_price, "isMarket": True, "tpsl": "sl"}},
    reduce_only=True)

# 3. 设置 +10% 止盈
profit_price = entry_price * 1.10
exchange.order("ETH", False, 0.1, profit_price*1.02,
    {"trigger": {"triggerPx": profit_price, "isMarket": True, "tpsl": "tp"}},
    reduce_only=True)
```

### 场景 4: 全部平仓

```python
# 市价平掉所有持仓
exchange.market_close("ETH")
```

---

## ⚠️ 重要提醒

### ✅ 正确做法

- ✅ 止损止盈设置 `reduce_only=True`
- ✅ 止损止盈使用 `isMarket=True`
- ✅ 开仓前先计算风险收益比
- ✅ 永远设置止损
- ✅ 在测试网充分练习

### ❌ 常见错误

- ❌ 止损忘记设置 `reduce_only=True`（会反向开仓！）
- ❌ 止损使用 `isMarket=False`（可能无法成交）
- ❌ 限价设置错误（止损限价应低于触发价）
- ❌ 没有设置止损就交易
- ❌ 直接在主网尝试

---

## 🔗 相关文档

- 详细教程: [ORDER_TYPES_GUIDE.md](ORDER_TYPES_GUIDE.md)
- 实践脚本: `python order_practice.py`
- 示例代码: [examples/](examples/)

---

## 💡 记忆口诀

**开仓**: `reduce_only=False`  
**平仓**: `reduce_only=True`

**做多止损**: 卖出 (`is_buy=False`)  
**做空止损**: 买入 (`is_buy=True`)

**触发后**: 用 `isMarket=True`  
**风险管理**: 永远第一位

