# 部署脚本说明

这个目录包含了在 Hostinger VPS 上自动部署 AI 交易机器人的脚本。

## 📁 文件说明

### 1. `setup_vps.sh` - 完整 VPS 初始化
**用途：** 全新 VPS 服务器的完整设置  
**运行者：** root 用户  
**功能：**
- 更新系统
- 安装必要软件（Python, Git, 等）
- 创建非 root 用户
- 配置防火墙
- 创建部署和监控脚本

**使用方法：**
```bash
# 1. 连接到 VPS
ssh root@your-vps-ip

# 2. 下载脚本
wget https://raw.githubusercontent.com/alexanderhanboli/hyperliquid-python-sdk/testnet/deploy/setup_vps.sh

# 3. 运行脚本
bash setup_vps.sh

# 4. 按提示操作
```

### 2. `quick_deploy.sh` - 快速部署机器人
**用途：** 在已配置好的系统上快速部署机器人  
**运行者：** 普通用户  
**功能：**
- 克隆代码
- 安装依赖
- 配置钱包和 API Key
- 运行测试
- 可选创建 systemd 服务

**使用方法：**
```bash
# 直接运行
wget https://raw.githubusercontent.com/alexanderhanboli/hyperliquid-python-sdk/testnet/deploy/quick_deploy.sh
bash quick_deploy.sh
```

## 🚀 推荐部署流程

### 方案 A: 全新 VPS（推荐）
适合刚购买的 Hostinger VPS

```bash
# 1. SSH 连接到 VPS
ssh root@your-vps-ip

# 2. 下载并运行完整设置脚本
wget https://raw.githubusercontent.com/alexanderhanboli/hyperliquid-python-sdk/testnet/deploy/setup_vps.sh
bash setup_vps.sh

# 3. 切换到新创建的用户
su - trader  # (或你设置的用户名)

# 4. 运行自动生成的部署脚本
./deploy_bot.sh

# 5. 创建服务
sudo ./create_service.sh

# 6. 监控机器人
./monitor_bot.sh
```

### 方案 B: 已有用户环境
如果你已经有一个配置好的用户

```bash
# 1. SSH 连接
ssh your-user@your-vps-ip

# 2. 下载并运行快速部署
wget https://raw.githubusercontent.com/alexanderhanboli/hyperliquid-python-sdk/testnet/deploy/quick_deploy.sh
bash quick_deploy.sh

# 3. 按提示输入配置
```

### 方案 C: 手动部署
如果你想完全控制每一步

参考 [HOSTINGER_DEPLOYMENT.md](../HOSTINGER_DEPLOYMENT.md)

## ⚙️ 配置项

部署时需要提供：

1. **Hyperliquid 配置**
   - 钱包地址
   - 私钥

2. **Anthropic API Key**
   - 从 https://console.anthropic.com/ 获取

3. **交易参数**（创建服务时）
   - 交易币种（如：BTC ETH SOL）
   - 交易间隔（分钟，如：3）

## 📊 部署后管理

### 查看机器人状态
```bash
sudo systemctl status ai-trading-bot
```

### 查看实时日志
```bash
tail -f ~/ai-trading-bot.log
```

### 停止机器人
```bash
sudo systemctl stop ai-trading-bot
```

### 重启机器人
```bash
sudo systemctl restart ai-trading-bot
```

### 更新代码
```bash
cd ~/hyperliquid-python-sdk
git pull origin testnet
sudo systemctl restart ai-trading-bot
```

## 🔒 安全提示

1. **保护私钥**
   - 配置文件权限已设置为 600
   - 不要分享配置文件
   - 定期备份

2. **防火墙**
   - 脚本会自动配置 UFW
   - 只开放必要端口（SSH）

3. **定期更新**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

## 🐛 故障排除

### 问题：服务启动失败
```bash
# 查看详细日志
sudo journalctl -u ai-trading-bot -xe

# 检查配置
cat ~/hyperliquid-python-sdk/examples/config.json
```

### 问题：API Key 错误
```bash
# 重新设置环境变量
nano ~/.bashrc
# 添加: export ANTHROPIC_API_KEY='your-key'
source ~/.bashrc

# 重启服务
sudo systemctl restart ai-trading-bot
```

### 问题：依赖安装失败
```bash
# 手动安装
cd ~/hyperliquid-python-sdk
source venv/bin/activate
pip install --upgrade pip
pip install numpy pandas anthropic schedule
```

## 📞 获取帮助

详细文档：
- [HOSTINGER_DEPLOYMENT.md](../HOSTINGER_DEPLOYMENT.md) - 完整部署指南
- [AI_TRADING_GUIDE.md](../AI_TRADING_GUIDE.md) - 使用指南
- [ai_trading/README.md](../ai_trading/README.md) - 系统架构

## 💡 提示

1. **先测试后运行**
   - 使用 `--test` 参数测试运行
   - 在测试网充分验证

2. **监控资源使用**
   ```bash
   htop  # 查看 CPU 和内存
   df -h # 查看磁盘空间
   ```

3. **设置备份**
   - 定期备份配置文件
   - 定期备份日志

4. **成本控制**
   - 调整 `--interval` 参数来控制 API 调用频率
   - 监控 Anthropic API 使用量

## 🎉 快速命令参考

```bash
# 查看状态
sudo systemctl status ai-trading-bot

# 启动
sudo systemctl start ai-trading-bot

# 停止
sudo systemctl stop ai-trading-bot

# 重启
sudo systemctl restart ai-trading-bot

# 查看日志
tail -f ~/ai-trading-bot.log

# 查看系统日志
sudo journalctl -u ai-trading-bot -f

# 监控脚本
./monitor_bot.sh

# 更新代码
cd ~/hyperliquid-python-sdk && git pull && sudo systemctl restart ai-trading-bot
```

---

**祝部署顺利！** 🚀

