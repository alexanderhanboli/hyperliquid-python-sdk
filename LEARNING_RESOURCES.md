# 📚 学习资源说明

本项目包含以下教程和工具文件，帮助你快速上手 Hyperliquid Python SDK。

---

## 📖 文档资源

### 1. QUICK_START.md
**快速上手指南** - 最全面的入门文档

- ✅ 项目结构说明
- ✅ 常用命令参考
- ✅ 示例代码分类
- ✅ 配置文件说明
- ✅ 学习路径建议

**推荐**: 新手从这里开始！

---

### 2. ORDER_TYPES_GUIDE.md
**订单类型详解** - 深入理解所有订单类型

- ✅ 限价单详解（Limit Order）
- ✅ 市价单详解（Market Order）
- ✅ 止损单详解（Stop Loss）
- ✅ 止盈单详解（Take Profit）
- ✅ 完整的代码示例
- ✅ 每个参数的详细说明

**适合**: 需要深入理解订单机制

---

### 3. ORDER_QUICK_REFERENCE.md
**订单快速参考** - 快速查找订单参数

- ✅ 参数速查表
- ✅ 常见场景代码
- ✅ 错误用法提醒
- ✅ 记忆口诀

**适合**: 作为日常编程的参考卡片

---

### 4. WALLET_EXPORT_GUIDE.md
**钱包私钥导出指南**

- ✅ MetaMask 导出方法
- ✅ 其他钱包导出方法
- ✅ 安全提醒

---

## 🛠️ 工具脚本

### 1. verify_setup.py
**配置验证工具** - 检查所有配置是否正确

```bash
python verify_setup.py
```

**功能**:
- ✅ 检查配置文件
- ✅ 验证私钥格式
- ✅ 验证地址匹配
- ✅ 测试网连接
- ✅ 查询账户余额
- ✅ 测试 Exchange 对象

---

### 2. test_connection.py
**连接测试脚本** - 测试网络连接（无需私钥）

```bash
python test_connection.py
```

**功能**:
- ✅ 查询市场价格
- ✅ 查询钱包状态
- ✅ 测试 API 连接

---

### 3. interactive_test.py
**交互式测试脚本** - 完整的功能测试

```bash
python interactive_test.py
```

**功能**:
- ✅ 查看账户状态
- ✅ 查看市场价格
- ✅ 查看未成交订单
- ✅ 测试下单和取消

---

### 4. order_practice.py
**订单类型实践脚本** - 逐步学习所有订单类型

```bash
python order_practice.py
```

**功能**:
- ✅ 示例 1: 限价单演示
- ✅ 示例 2: 市价单原理
- ✅ 示例 3: 止损单演示
- ✅ 示例 4: 止盈单演示
- ✅ 示例 5: 完整交易策略

**推荐**: 理解订单类型的最佳方式！

---

## 📁 使用流程建议

### 第一次使用

1. **阅读快速上手指南**
   ```bash
   cat QUICK_START.md
   ```

2. **验证配置**
   ```bash
   python verify_setup.py
   ```

3. **测试连接**（可选，无需私钥）
   ```bash
   python test_connection.py
   ```

### 学习订单类型

1. **快速参考**（5分钟）
   ```bash
   cat ORDER_QUICK_REFERENCE.md
   ```

2. **详细教程**（20分钟）
   ```bash
   cat ORDER_TYPES_GUIDE.md
   ```

3. **实践练习**
   ```bash
   python order_practice.py
   ```

### 日常开发

1. **快速查找参数**
   ```bash
   grep -A 5 "止损单" ORDER_QUICK_REFERENCE.md
   ```

2. **运行测试**
   ```bash
   python interactive_test.py
   ```

3. **查看示例**
   ```bash
   cd examples
   python basic_order.py
   ```

---

## 🔄 与官方示例的关系

### 官方示例 (examples/)
- 来自官方 SDK
- 更全面的功能演示
- 适合查看特定功能实现

### 本地工具脚本
- 更友好的学习工具
- 带有详细说明
- 更安全的测试环境
- 中文注释和说明

**建议**: 先用本地工具学习，再看官方示例深入

---

## 📊 文件大小和内容

| 文件 | 大小 | 行数 | 类型 |
|------|------|------|------|
| QUICK_START.md | 6.9KB | 286 | 文档 |
| ORDER_TYPES_GUIDE.md | 14KB | 547 | 文档 |
| ORDER_QUICK_REFERENCE.md | 5.3KB | 261 | 文档 |
| WALLET_EXPORT_GUIDE.md | 766B | 35 | 文档 |
| verify_setup.py | 4.6KB | 145 | 工具 |
| test_connection.py | 2.0KB | 64 | 工具 |
| interactive_test.py | 4.2KB | 126 | 工具 |
| order_practice.py | 12KB | 345 | 教程 |

**总计**: ~50KB 的学习资源！

---

## 🎯 适用场景

| 场景 | 推荐资源 |
|------|---------|
| 第一次使用 SDK | QUICK_START.md |
| 验证环境配置 | verify_setup.py |
| 测试网络连接 | test_connection.py |
| 学习订单类型 | order_practice.py |
| 快速查找参数 | ORDER_QUICK_REFERENCE.md |
| 深入理解机制 | ORDER_TYPES_GUIDE.md |
| 日常开发参考 | ORDER_QUICK_REFERENCE.md |
| 导出钱包私钥 | WALLET_EXPORT_GUIDE.md |

---

## ⚠️ 注意事项

1. **所有脚本默认使用测试网**
   - 不会影响真实资金
   - 需要先获取测试币

2. **配置文件已被 .gitignore**
   - `examples/config.json` 不会被提交
   - 私钥安全有保障

3. **文档持续更新**
   - 如有疑问或建议，欢迎反馈

---

## 🤝 贡献

这些学习资源是为了帮助新手快速上手。如果你有改进建议：

1. 提交 Issue 描述问题
2. 或直接提交 Pull Request
3. 或联系项目维护者

---

## 📞 获取帮助

如果遇到问题：

1. 先查看 QUICK_START.md 的常见问题部分
2. 运行 `python verify_setup.py` 检查配置
3. 查看 ORDER_TYPES_GUIDE.md 确认参数用法
4. 加入 Hyperliquid Discord 社区
5. 查看官方文档

---

**祝你学习愉快！🚀**

