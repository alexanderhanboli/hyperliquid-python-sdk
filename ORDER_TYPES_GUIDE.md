# 📖 Hyperliquid 订单类型详解

完整的限价单、止盈止损参数说明和代码示例

---

## 📋 目录

1. [基础订单方法](#基础订单方法)
2. [限价单 (Limit Order)](#限价单-limit-order)
3. [市价单 (Market Order)](#市价单-market-order)
4. [止损单 (Stop Loss)](#止损单-stop-loss)
5. [止盈单 (Take Profit)](#止盈单-take-profit)
6. [完整示例](#完整示例)

---

## 基础订单方法

### `exchange.order()` 方法签名

```python
def order(
    self,
    name: str,              # 币种名称
    is_buy: bool,           # True=买入, False=卖出
    sz: float,              # 数量
    limit_px: float,        # 限价价格
    order_type: OrderType,  # 订单类型
    reduce_only: bool = False,  # 只减仓模式
    cloid: Optional[Cloid] = None,  # 客户端订单ID
    builder: Optional[BuilderInfo] = None,  # 构建者信息
) -> Any:
```

### 参数详解

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| **name** | `str` | 交易币种符号 | `"ETH"`, `"BTC"`, `"SOL"` |
| **is_buy** | `bool` | 买入或卖出方向 | `True`(买), `False`(卖) |
| **sz** | `float` | 订单数量 | `0.1`, `1.5`, `10.0` |
| **limit_px** | `float` | 限价价格（USD） | `3000.0`, `1500.5` |
| **order_type** | `OrderType` | 订单类型（详见下文） | `{"limit": {...}}` |
| **reduce_only** | `bool` | 是否只减仓（默认False） | `True`, `False` |
| **cloid** | `Optional[Cloid]` | 客户端订单ID（可选） | `None` 或自定义ID |
| **builder** | `Optional[BuilderInfo]` | 构建者费用信息（高级） | 通常为 `None` |

---

## 限价单 (Limit Order)

限价单允许你指定一个价格，只有当市场价格达到或优于你的价格时才会成交。

### 📌 基本概念

- **买入限价单**: 当市场价 ≤ 你的限价时成交
- **卖出限价单**: 当市场价 ≥ 你的限价时成交
- **优势**: 价格可控，不会滑点过大
- **劣势**: 可能不成交

### 🔧 参数结构

```python
order_type = {
    "limit": {
        "tif": "Gtc"  # Time In Force (订单有效期)
    }
}
```

### 📝 TIF (Time In Force) 选项

| TIF 值 | 全称 | 说明 |
|--------|------|------|
| **`"Gtc"`** | Good Till Cancel | 一直有效直到成交或取消（最常用） |
| **`"Ioc"`** | Immediate Or Cancel | 立即成交，未成交部分立即取消 |
| **`"Alo"`** | Add Liquidity Only | 只做市商，确保不会立即成交 |

### 💻 代码示例

#### 示例 1: 买入限价单

```python
# 以 $3000 的价格买入 0.5 ETH
result = exchange.order(
    name="ETH",           # 币种: ETH
    is_buy=True,          # 买入
    sz=0.5,               # 数量: 0.5 ETH
    limit_px=3000.0,      # 限价: $3000
    order_type={"limit": {"tif": "Gtc"}},  # 普通限价单
    reduce_only=False     # 可以开新仓位
)
```

**解释**:
- 当 ETH 价格 ≤ $3000 时，订单会成交
- 如果当前价格是 $3500，订单会挂在订单簿上等待
- 订单会一直保留直到成交或手动取消

#### 示例 2: 卖出限价单

```python
# 以 $4000 的价格卖出 0.3 ETH
result = exchange.order(
    name="ETH",
    is_buy=False,         # 卖出
    sz=0.3,
    limit_px=4000.0,      # 限价: $4000
    order_type={"limit": {"tif": "Gtc"}},
    reduce_only=False
)
```

**解释**:
- 当 ETH 价格 ≥ $4000 时，订单会成交
- 如果当前价格是 $3500，订单会等待价格上涨

#### 示例 3: 立即成交或取消 (IoC)

```python
# 尝试立即以 $3500 买入 0.2 ETH，不能成交就取消
result = exchange.order(
    name="ETH",
    is_buy=True,
    sz=0.2,
    limit_px=3500.0,
    order_type={"limit": {"tif": "Ioc"}},  # IoC 模式
    reduce_only=False
)
```

**解释**:
- 如果有人以 ≤ $3500 卖出，立即成交
- 如果没有匹配的订单，立即取消，不会挂单

#### 示例 4: 只做市商模式 (Alo)

```python
# 挂单做市，确保不会立即成交
result = exchange.order(
    name="ETH",
    is_buy=True,
    sz=0.1,
    limit_px=3000.0,
    order_type={"limit": {"tif": "Alo"}},  # 只做市商
    reduce_only=False
)
```

**解释**:
- 确保订单只会挂在订单簿上，不会作为"吃单方"
- 可以获得做市商费率优惠
- 如果价格会立即成交，订单会被拒绝

---

## 市价单 (Market Order)

市价单会立即以当前最优价格成交。

### 📌 基本概念

- **买入市价单**: 立即以卖方最低价买入
- **卖出市价单**: 立即以买方最高价卖出
- **优势**: 立即成交，快速建仓/平仓
- **劣势**: 可能有滑点，价格不可控

### 🔧 实现方式

Hyperliquid 的市价单实际上是**激进的限价单**:

```python
def market_open(
    name: str,
    is_buy: bool,
    sz: float,
    px: Optional[float] = None,      # 可选的参考价格
    slippage: float = DEFAULT_SLIPPAGE,  # 滑点容忍度（默认5%）
    ...
):
    # 计算一个激进的限价
    # 买入: 当前价 * (1 + slippage)
    # 卖出: 当前价 * (1 - slippage)
    px = self._slippage_price(name, is_buy, slippage, px)
    
    # 使用 IoC 限价单
    return self.order(
        name, is_buy, sz, px,
        order_type={"limit": {"tif": "Ioc"}},
        reduce_only=False
    )
```

### 💻 代码示例

#### 示例 1: 市价买入

```python
# 市价买入 0.1 ETH（默认 5% 滑点容忍）
result = exchange.market_open(
    coin="ETH",
    is_buy=True,
    sz=0.1
)
```

**实际操作**:
1. 查询当前 ETH 价格，假设是 $3000
2. 计算限价: $3000 × 1.05 = $3150
3. 以 IoC 限价单 $3150 买入
4. 立即以最优价格成交（通常接近 $3000）

#### 示例 2: 市价卖出（平仓）

```python
# 市价平掉所有 ETH 持仓
result = exchange.market_close(coin="ETH")
```

**解释**:
- 自动查询当前 ETH 持仓
- 计算需要平仓的数量
- 以市价卖出（如果是多仓）或买入（如果是空仓）

#### 示例 3: 自定义滑点

```python
# 市价买入，但只接受 1% 滑点
result = exchange.market_open(
    coin="ETH",
    is_buy=True,
    sz=0.1,
    slippage=0.01  # 1% 滑点
)
```

---

## 止损单 (Stop Loss)

止损单是一种条件订单，当价格达到触发价时自动执行，用于限制损失。

### 📌 基本概念

- **做多止损**: 当价格跌到止损价时，自动**卖出**平仓
- **做空止损**: 当价格涨到止损价时，自动**买入**平仓
- **目的**: 自动止损，保护资金

### 🔧 参数结构

```python
order_type = {
    "trigger": {
        "triggerPx": 2800.0,    # 触发价格
        "isMarket": True,        # 是否市价成交
        "tpsl": "sl"            # 标记为止损单
    }
}
```

### 📝 参数详解

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| **triggerPx** | `float` | 触发价格 | `2800.0` |
| **isMarket** | `bool` | True=触发后市价成交, False=限价成交 | `True` (推荐) |
| **tpsl** | `str` | `"sl"` 表示止损, `"tp"` 表示止盈 | `"sl"` |

### 💻 代码示例

#### 示例 1: 做多止损

```python
# 假设你以 $3000 买入了 0.5 ETH
# 现在设置止损价 $2800（亏损 $200/ETH）

result = exchange.order(
    name="ETH",
    is_buy=False,           # 止损是卖出
    sz=0.5,                 # 平掉 0.5 ETH
    limit_px=2700.0,        # 限价（低于触发价，确保成交）
    order_type={
        "trigger": {
            "triggerPx": 2800.0,   # 当价格跌到 $2800
            "isMarket": True,       # 触发后市价卖出
            "tpsl": "sl"           # 标记为止损
        }
    },
    reduce_only=True        # ⚠️ 重要：只减仓，不开新空仓
)
```

**工作流程**:
1. ETH 价格为 $3000，订单挂单等待
2. 当价格跌到 $2800 时，**触发**止损
3. 立即以市价卖出 0.5 ETH
4. 锁定损失在 $200/ETH 以内

#### 示例 2: 做空止损

```python
# 假设你以 $3000 做空了 0.5 ETH
# 设置止损价 $3200（亏损 $200/ETH）

result = exchange.order(
    name="ETH",
    is_buy=True,            # 止损是买入平空
    sz=0.5,
    limit_px=3300.0,        # 限价（高于触发价）
    order_type={
        "trigger": {
            "triggerPx": 3200.0,   # 当价格涨到 $3200
            "isMarket": True,
            "tpsl": "sl"
        }
    },
    reduce_only=True
)
```

---

## 止盈单 (Take Profit)

止盈单与止损单类似，但用于锁定利润。

### 📌 基本概念

- **做多止盈**: 当价格涨到目标价时，自动**卖出**获利
- **做空止盈**: 当价格跌到目标价时，自动**买入**获利
- **目的**: 自动止盈，锁定利润

### 🔧 参数结构

```python
order_type = {
    "trigger": {
        "triggerPx": 3500.0,    # 触发价格
        "isMarket": True,        # 市价成交
        "tpsl": "tp"            # 标记为止盈单
    }
}
```

### 💻 代码示例

#### 示例 1: 做多止盈

```python
# 假设你以 $3000 买入了 0.5 ETH
# 设置止盈价 $3500（盈利 $500/ETH）

result = exchange.order(
    name="ETH",
    is_buy=False,           # 止盈是卖出
    sz=0.5,
    limit_px=3400.0,        # 限价（低于触发价一点）
    order_type={
        "trigger": {
            "triggerPx": 3500.0,   # 当价格涨到 $3500
            "isMarket": True,
            "tpsl": "tp"           # 标记为止盈
        }
    },
    reduce_only=True
)
```

#### 示例 2: 做空止盈

```python
# 假设你以 $3000 做空了 0.5 ETH
# 设置止盈价 $2500（盈利 $500/ETH）

result = exchange.order(
    name="ETH",
    is_buy=True,            # 止盈是买入平空
    sz=0.5,
    limit_px=2600.0,        # 限价（高于触发价一点）
    order_type={
        "trigger": {
            "triggerPx": 2500.0,   # 当价格跌到 $2500
            "isMarket": True,
            "tpsl": "tp"
        }
    },
    reduce_only=True
)
```

---

## 完整示例

### 综合示例：完整的交易流程

```python
import example_utils
from hyperliquid.utils import constants

def trading_example():
    """完整的交易示例：开仓 + 止损 + 止盈"""
    
    # 1. 初始化
    address, info, exchange = example_utils.setup(
        base_url=constants.TESTNET_API_URL, 
        skip_ws=True
    )
    
    # 2. 查询当前价格
    all_mids = info.all_mids()
    current_price = float(all_mids["ETH"])
    print(f"当前 ETH 价格: ${current_price}")
    
    # 3. 开仓：限价买入
    entry_price = current_price * 0.98  # 比当前价低 2%
    position_size = 0.1
    
    print(f"\n步骤 1: 限价买入 {position_size} ETH @ ${entry_price:.2f}")
    
    order_result = exchange.order(
        name="ETH",
        is_buy=True,
        sz=position_size,
        limit_px=entry_price,
        order_type={"limit": {"tif": "Gtc"}},
        reduce_only=False
    )
    
    if order_result["status"] == "ok":
        print("✅ 限价买单已挂单")
        oid = order_result["response"]["data"]["statuses"][0]["resting"]["oid"]
        print(f"   订单ID: {oid}")
    
    # 4. 设置止损（假设已成交）
    stop_loss_price = entry_price * 0.95  # -5% 止损
    
    print(f"\n步骤 2: 设置止损 @ ${stop_loss_price:.2f}")
    
    sl_result = exchange.order(
        name="ETH",
        is_buy=False,              # 卖出
        sz=position_size,
        limit_px=stop_loss_price * 0.98,  # 稍低于触发价
        order_type={
            "trigger": {
                "triggerPx": stop_loss_price,
                "isMarket": True,
                "tpsl": "sl"
            }
        },
        reduce_only=True           # ⚠️ 只减仓
    )
    
    if sl_result["status"] == "ok":
        print("✅ 止损单已设置")
    
    # 5. 设置止盈
    take_profit_price = entry_price * 1.10  # +10% 止盈
    
    print(f"\n步骤 3: 设置止盈 @ ${take_profit_price:.2f}")
    
    tp_result = exchange.order(
        name="ETH",
        is_buy=False,
        sz=position_size,
        limit_px=take_profit_price * 1.02,
        order_type={
            "trigger": {
                "triggerPx": take_profit_price,
                "isMarket": True,
                "tpsl": "tp"
            }
        },
        reduce_only=True
    )
    
    if tp_result["status"] == "ok":
        print("✅ 止盈单已设置")
    
    # 6. 查询所有订单
    print("\n步骤 4: 查询所有挂单")
    open_orders = info.open_orders(address)
    print(f"当前有 {len(open_orders)} 个挂单:")
    for order in open_orders:
        order_type = "买入" if order["side"] == "B" else "卖出"
        print(f"  {order['coin']} {order_type} {order['sz']} @ ${order['limitPx']}")
    
    # 7. 总结
    print("\n" + "="*60)
    print("交易设置完成!")
    print(f"入场价: ${entry_price:.2f}")
    print(f"止损价: ${stop_loss_price:.2f} (风险: {-5}%)")
    print(f"止盈价: ${take_profit_price:.2f} (收益: {+10}%)")
    print(f"风险收益比: 1:2")
    print("="*60)

if __name__ == "__main__":
    trading_example()
```

---

## 🎯 重要提示

### ⚠️ reduce_only 参数

- **`reduce_only=True`**: 只能减少现有仓位，不能开新仓
  - ✅ 用于止损、止盈
  - ✅ 防止反向开仓
  
- **`reduce_only=False`**: 可以开新仓位
  - ✅ 用于入场订单
  - ⚠️ 不要用于止损/止盈

### 💡 最佳实践

1. **止损止盈使用 `isMarket=True`**
   - 确保触发后能立即成交
   - 避免滑点导致无法平仓

2. **限价要合理**
   - 止损限价 < 触发价（做多）
   - 止盈限价 > 触发价（做多）

3. **始终设置止损**
   - 保护资金安全
   - 控制每笔交易的风险

4. **测试网充分测试**
   - 在测试网验证所有逻辑
   - 确保理解每个参数

---

## 📚 参考资料

- [Hyperliquid 官方文档](https://hyperliquid.gitbook.io/)
- [SDK GitHub](https://github.com/hyperliquid-dex/hyperliquid-python-sdk)
- [示例代码](../examples/)

---

需要更多帮助？查看 `examples/` 目录中的实际例子！

