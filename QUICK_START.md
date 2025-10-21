# 🚀 Hyperliquid Python SDK 快速上手指南

## ✅ 你已经完成的设置

- ✅ 创建虚拟环境
- ✅ 安装依赖包
- ✅ 配置私钥和钱包地址
- ✅ 获取测试币（$999.0）
- ✅ 成功运行第一笔测试交易

---

## 📁 项目结构

```
hyperliquid-python-sdk/
├── hyperliquid/              # SDK 核心代码
│   ├── info.py              # 查询市场数据和账户信息
│   ├── exchange.py          # 执行交易操作
│   └── utils/               # 工具函数
├── examples/                # 示例代码
│   ├── config.json          # 你的配置文件（已配置）
│   ├── basic_*.py           # 基础示例
│   └── example_utils.py     # 示例工具函数
├── tests/                   # 单元测试
├── test_connection.py       # 连接测试脚本
├── verify_setup.py          # 配置验证脚本
└── interactive_test.py      # 交互式测试脚本
```

---

## 🎯 常用命令

### 激活虚拟环境
```bash
cd /Users/hanboli/Projects/hyperliquid-python-sdk
source venv/bin/activate
```

### 运行测试脚本
```bash
# 测试连接（只读，无需私钥）
python test_connection.py

# 验证配置
python verify_setup.py

# 交互式测试（查询+下单+取消）
python interactive_test.py
```

### 运行示例代码
```bash
cd examples

# 基础示例
python basic_order.py              # 限价单
python basic_market_order.py       # 市价单
python basic_order_modify.py       # 修改订单
python cancel_open_orders.py       # 取消所有订单

# 高级功能
python basic_leverage_adjustment.py  # 调整杠杆
python basic_tpsl.py                # 止盈止损
python basic_spot_order.py          # 现货交易
python basic_transfer.py            # 资金转账
```

---

## 📚 常用示例说明

### 1. 基础交易
| 文件 | 功能 | 难度 |
|------|------|------|
| `basic_order.py` | 限价单（买入/卖出） | ⭐ |
| `basic_market_order.py` | 市价单（快速成交） | ⭐ |
| `basic_order_modify.py` | 修改现有订单 | ⭐⭐ |
| `cancel_open_orders.py` | 取消所有未成交订单 | ⭐ |

### 2. 仓位管理
| 文件 | 功能 | 难度 |
|------|------|------|
| `basic_leverage_adjustment.py` | 调整杠杆倍数 | ⭐⭐ |
| `basic_tpsl.py` | 设置止盈止损 | ⭐⭐ |

### 3. 现货交易
| 文件 | 功能 | 难度 |
|------|------|------|
| `basic_spot_order.py` | 现货买卖 | ⭐ |
| `basic_spot_transfer.py` | 现货转账 | ⭐ |
| `basic_spot_to_perp.py` | 现货转合约 | ⭐⭐ |

### 4. 资金管理
| 文件 | 功能 | 难度 |
|------|------|------|
| `basic_transfer.py` | 资金转账 | ⭐ |
| `basic_send_asset.py` | 发送资产 | ⭐⭐ |
| `basic_withdraw.py` | 提现 | ⭐⭐ |

### 5. 高级功能
| 文件 | 功能 | 难度 |
|------|------|------|
| `basic_agent.py` | API 代理钱包 | ⭐⭐⭐ |
| `basic_sub_account.py` | 子账户管理 | ⭐⭐⭐ |
| `basic_vault.py` | 资金池操作 | ⭐⭐⭐ |
| `basic_staking.py` | 质押操作 | ⭐⭐ |

---

## 💻 代码示例

### 查询市场价格（只读，无需私钥）
```python
from hyperliquid.info import Info
from hyperliquid.utils import constants

info = Info(constants.TESTNET_API_URL, skip_ws=True)

# 获取所有币种价格
all_mids = info.all_mids()
print(f"BTC 价格: ${all_mids['BTC']}")
print(f"ETH 价格: ${all_mids['ETH']}")
```

### 查询账户状态
```python
from hyperliquid.info import Info
from hyperliquid.utils import constants

info = Info(constants.TESTNET_API_URL, skip_ws=True)
address = "0xef6b0240e25b7880ab26f54c8c63034e4ac4f844"

user_state = info.user_state(address)
account_value = user_state["marginSummary"]["accountValue"]
print(f"账户价值: ${account_value}")
```

### 下限价单（需要私钥）
```python
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants
import eth_account

# 加载私钥
account = eth_account.Account.from_key("你的私钥")
exchange = Exchange(account, base_url=constants.TESTNET_API_URL)

# 下单：买入 0.1 ETH，价格 $3000
result = exchange.order(
    "ETH",           # 币种
    True,            # True=买入, False=卖出
    0.1,             # 数量
    3000,            # 价格
    {"limit": {"tif": "Gtc"}}  # 订单类型
)
print(result)
```

### 下市价单
```python
# 市价买入 0.05 ETH
result = exchange.market_open("ETH", True, 0.05)
print(result)
```

### 取消订单
```python
# 取消指定订单
exchange.cancel("ETH", order_id)

# 或查询所有订单后取消
open_orders = info.open_orders(address)
for order in open_orders:
    exchange.cancel(order['coin'], order['oid'])
```

---

## 🔧 配置文件说明

### `examples/config.json`
```json
{
    "keystore_path": "",
    "secret_key": "你的私钥",
    "account_address": "0xef6b0240e25b7880ab26f54c8c63034e4ac4f844"
}
```

- `secret_key`: 钱包私钥（必填）
- `account_address`: 钱包地址（可选，会自动从私钥推导）
- `keystore_path`: Keystore 文件路径（可选，替代私钥）

---

## 🌐 重要 URL

### 测试网
- 网站: https://app.hyperliquid-testnet.xyz
- API: https://api.hyperliquid-testnet.xyz

### 主网
- 网站: https://app.hyperliquid.xyz
- API: https://api.hyperliquid.xyz

### 文档和社区
- SDK 文档: https://github.com/hyperliquid-dex/hyperliquid-python-sdk
- Discord: https://discord.gg/hyperliquid
- Twitter: https://twitter.com/HyperliquidX

---

## ⚠️ 安全提示

1. **只在测试网使用测试钱包**
2. **不要在代码中硬编码私钥**
3. **不要提交 config.json 到 Git**（已在 .gitignore）
4. **不要分享私钥给任何人**
5. **主网交易前充分测试**

---

## 🐛 常见问题

### Q: 如何切换到主网？
A: 将 `constants.TESTNET_API_URL` 改为 `constants.MAINNET_API_URL`

### Q: 如何获取更多测试币？
A: 测试网只能领取一次，需要在主网有存款记录

### Q: 订单一直不成交怎么办？
A: 检查价格是否合理，限价单需要价格匹配才能成交

### Q: 如何查看交易历史？
```python
fills = info.user_fills(address)
print(fills)
```

### Q: 如何设置止损？
```python
# 查看 examples/basic_tpsl.py 示例
```

---

## 📖 学习路径

1. ✅ **完成基础设置**（你已经完成！）
2. 🎯 **运行所有 basic_*.py 示例**
3. 📝 **阅读 SDK 源码**: `hyperliquid/info.py` 和 `hyperliquid/exchange.py`
4. 🔨 **修改示例代码**，尝试不同参数
5. 🚀 **开发自己的交易策略**
6. 💡 **在主网小额测试**
7. 🎓 **持续优化和学习**

---

## 🎉 下一步

现在你可以：

1. **运行更多示例**
   ```bash
   cd examples
   python basic_market_order.py
   ```

2. **查看账户状态**
   ```bash
   python ../interactive_test.py
   ```

3. **开始开发自己的策略**
   - 复制一个示例文件
   - 修改交易逻辑
   - 在测试网验证

4. **阅读官方文档**
   - https://hyperliquid.gitbook.io/hyperliquid-docs

祝你交易顺利！🚀

