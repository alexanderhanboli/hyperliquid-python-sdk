# Hostinger VPS 部署指南

## 📋 准备工作

### 1. Hostinger VPS 配置建议

**最低配置:**
- CPU: 1 核
- RAM: 2GB
- 存储: 20GB SSD
- 操作系统: Ubuntu 22.04 LTS

**推荐配置（运行多个机器人）:**
- CPU: 2 核
- RAM: 4GB
- 存储: 40GB SSD

## 🚀 部署步骤

### 步骤 1: 连接到 Hostinger VPS

#### 1.1 获取 VPS 登录信息
登录 Hostinger 控制面板，找到：
- IP 地址
- SSH 端口（通常是 22）
- root 密码

#### 1.2 通过 SSH 连接
```bash
ssh root@your-vps-ip
# 输入密码
```

### 步骤 2: 服务器初始设置

#### 2.1 更新系统
```bash
apt update && apt upgrade -y
```

#### 2.2 安装必要软件
```bash
# 安装 Python 3.9+ 和 pip
apt install python3 python3-pip python3-venv git -y

# 验证安装
python3 --version
pip3 --version
```

#### 2.3 创建非 root 用户（推荐）
```bash
# 创建用户
adduser trader
usermod -aG sudo trader

# 切换到新用户
su - trader
```

### 步骤 3: 部署 AI 交易机器人

#### 3.1 克隆代码
```bash
cd ~
git clone https://github.com/alexanderhanboli/hyperliquid-python-sdk.git
cd hyperliquid-python-sdk
git checkout testnet
```

#### 3.2 创建虚拟环境
```bash
python3 -m venv venv
source venv/bin/activate
```

#### 3.3 安装依赖
```bash
pip install --upgrade pip
pip install numpy pandas anthropic schedule
pip install -e .
```

#### 3.4 配置文件设置

**配置 Hyperliquid:**
```bash
cd examples
cp config.json.example config.json
nano config.json
```

编辑内容：
```json
{
  "account_address": "0xYourWalletAddress",
  "secret_key": "YourPrivateKey"
}
```

保存：`Ctrl+X`, `Y`, `Enter`

**设置环境变量:**
```bash
# 创建环境变量文件
nano ~/.bashrc

# 在文件末尾添加
export ANTHROPIC_API_KEY='your-anthropic-api-key'

# 保存后重新加载
source ~/.bashrc
```

### 步骤 4: 测试运行

#### 4.1 运行系统测试
```bash
cd ~/hyperliquid-python-sdk
source venv/bin/activate
python ai_trading/test_system.py
```

应该看到所有测试通过 ✅

#### 4.2 测试模式运行
```bash
python ai_trading/ai_trader_bot.py --test
```

### 步骤 5: 使用 systemd 创建后台服务

#### 5.1 创建服务文件
```bash
sudo nano /etc/systemd/system/ai-trading-bot.service
```

#### 5.2 服务配置
```ini
[Unit]
Description=AI Trading Bot - Hyperliquid
After=network.target

[Service]
Type=simple
User=trader
WorkingDirectory=/home/trader/hyperliquid-python-sdk
Environment="ANTHROPIC_API_KEY=your-api-key-here"
ExecStart=/home/trader/hyperliquid-python-sdk/venv/bin/python ai_trading/ai_trader_bot.py --coins BTC ETH SOL --interval 3
Restart=always
RestartSec=10

# 日志配置
StandardOutput=append:/home/trader/ai-trading-bot.log
StandardError=append:/home/trader/ai-trading-bot-error.log

[Install]
WantedBy=multi-user.target
```

**重要：** 替换以下内容：
- `your-api-key-here` → 你的 Anthropic API Key
- `/home/trader` → 你的实际用户目录
- `--coins BTC ETH SOL` → 你想交易的币种
- `--interval 3` → 交易间隔（分钟）

#### 5.3 启动服务
```bash
# 重新加载 systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start ai-trading-bot

# 设置开机自启
sudo systemctl enable ai-trading-bot

# 查看状态
sudo systemctl status ai-trading-bot
```

#### 5.4 管理服务
```bash
# 停止服务
sudo systemctl stop ai-trading-bot

# 重启服务
sudo systemctl restart ai-trading-bot

# 查看日志
tail -f ~/ai-trading-bot.log

# 查看错误日志
tail -f ~/ai-trading-bot-error.log

# 查看实时系统日志
sudo journalctl -u ai-trading-bot -f
```

### 步骤 6: 使用 Screen（备选方案）

如果不想用 systemd，可以使用 screen：

#### 6.1 安装 screen
```bash
sudo apt install screen -y
```

#### 6.2 创建启动脚本
```bash
nano ~/start-trading-bot.sh
```

内容：
```bash
#!/bin/bash
cd ~/hyperliquid-python-sdk
source venv/bin/activate
export ANTHROPIC_API_KEY='your-api-key'
python ai_trading/ai_trader_bot.py --coins BTC ETH SOL --interval 3
```

```bash
chmod +x ~/start-trading-bot.sh
```

#### 6.3 使用 screen 运行
```bash
# 创建一个名为 trading 的 screen 会话
screen -S trading

# 运行脚本
./start-trading-bot.sh

# 断开连接（机器人继续运行）
# 按 Ctrl+A，然后按 D
```

#### 6.4 管理 screen 会话
```bash
# 查看所有 screen 会话
screen -ls

# 重新连接到 trading 会话
screen -r trading

# 停止机器人
# 在 screen 内按 Ctrl+C

# 删除 screen 会话
screen -X -S trading quit
```

## 📊 监控和维护

### 1. 查看日志

**systemd 服务日志:**
```bash
# 实时查看应用日志
tail -f ~/ai-trading-bot.log

# 查看最近 100 行
tail -n 100 ~/ai-trading-bot.log

# 查看系统日志
sudo journalctl -u ai-trading-bot -n 100
```

**Screen 日志:**
```bash
# 重新连接到 screen 查看输出
screen -r trading
```

### 2. 监控脚本

创建监控脚本 `~/monitor-bot.sh`：
```bash
#!/bin/bash

echo "=== AI Trading Bot Status ==="
echo ""

# 检查服务状态
echo "Service Status:"
sudo systemctl is-active ai-trading-bot
echo ""

# 检查最后 5 行日志
echo "Last 5 log lines:"
tail -n 5 ~/ai-trading-bot.log
echo ""

# 检查内存使用
echo "Memory Usage:"
ps aux | grep ai_trader_bot.py | grep -v grep
echo ""

# 检查磁盘空间
echo "Disk Space:"
df -h | grep -E '^/dev/'
```

```bash
chmod +x ~/monitor-bot.sh
./monitor-bot.sh
```

### 3. 设置 Cron 定时监控（可选）

每小时检查一次：
```bash
crontab -e

# 添加
0 * * * * /home/trader/monitor-bot.sh >> /home/trader/monitor.log 2>&1
```

## 🔒 安全建议

### 1. 配置防火墙
```bash
# 安装 UFW
sudo apt install ufw -y

# 允许 SSH
sudo ufw allow 22/tcp

# 如果需要 HTTP/HTTPS（用于监控界面）
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 启用防火墙
sudo ufw enable

# 查看状态
sudo ufw status
```

### 2. 保护私钥
```bash
# 设置配置文件权限
chmod 600 ~/hyperliquid-python-sdk/examples/config.json

# 确保只有你能读取
ls -la ~/hyperliquid-python-sdk/examples/config.json
```

### 3. 定期备份
```bash
# 创建备份脚本
nano ~/backup-bot.sh
```

内容：
```bash
#!/bin/bash
BACKUP_DIR=~/backups
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 备份配置文件
cp ~/hyperliquid-python-sdk/examples/config.json $BACKUP_DIR/config_$DATE.json

# 备份日志
cp ~/ai-trading-bot.log $BACKUP_DIR/log_$DATE.log

# 备份 AI 决策记录
cp ~/hyperliquid-python-sdk/ai_trading/last_prompt.txt $BACKUP_DIR/prompt_$DATE.txt
cp ~/hyperliquid-python-sdk/ai_trading/last_decision.json $BACKUP_DIR/decision_$DATE.json

# 删除 30 天前的备份
find $BACKUP_DIR -mtime +30 -delete

echo "Backup completed: $DATE"
```

```bash
chmod +x ~/backup-bot.sh

# 设置每天凌晨 3 点备份
crontab -e
# 添加
0 3 * * * /home/trader/backup-bot.sh >> /home/trader/backup.log 2>&1
```

## 🔧 故障排除

### 问题 1: 服务启动失败
```bash
# 查看详细错误
sudo journalctl -u ai-trading-bot -xe

# 检查配置文件
cat /etc/systemd/system/ai-trading-bot.service

# 检查 Python 路径
which python3
```

### 问题 2: API Key 错误
```bash
# 验证环境变量
echo $ANTHROPIC_API_KEY

# 重新设置
export ANTHROPIC_API_KEY='your-key'

# 或者在服务文件中直接设置
sudo nano /etc/systemd/system/ai-trading-bot.service
```

### 问题 3: 网络连接问题
```bash
# 测试网络
ping -c 4 api.hyperliquid.xyz

# 检查 DNS
nslookup api.hyperliquid.xyz

# 如果有问题，使用 Google DNS
sudo nano /etc/resolv.conf
# 添加
nameserver 8.8.8.8
nameserver 8.8.4.4
```

### 问题 4: 内存不足
```bash
# 查看内存使用
free -h

# 创建 swap（如果 RAM < 2GB）
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 永久启用
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

## 📱 远程监控（可选）

### 使用 Telegram Bot 监控

创建 Telegram 通知脚本 `~/telegram-notify.py`：
```python
#!/usr/bin/env python3
import requests
import sys

TELEGRAM_BOT_TOKEN = 'your-bot-token'
TELEGRAM_CHAT_ID = 'your-chat-id'

def send_message(message):
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
    requests.post(url, data=data)

if __name__ == '__main__':
    message = ' '.join(sys.argv[1:])
    send_message(message)
```

使用：
```bash
chmod +x ~/telegram-notify.py
./telegram-notify.py "AI Trading Bot started successfully!"
```

## 📊 性能优化

### 1. 限制日志大小
```bash
# 在服务文件中添加日志轮转
sudo nano /etc/systemd/system/ai-trading-bot.service

# 添加到 [Service] 部分
StandardOutputFileMaxSize=10M
StandardErrorFileMaxSize=10M
```

### 2. 使用 logrotate
```bash
sudo nano /etc/logrotate.d/ai-trading-bot
```

内容：
```
/home/trader/ai-trading-bot.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
```

## 🔄 更新部署

当有新代码时：
```bash
# 停止服务
sudo systemctl stop ai-trading-bot

# 更新代码
cd ~/hyperliquid-python-sdk
git pull origin testnet

# 更新依赖（如果需要）
source venv/bin/activate
pip install --upgrade numpy pandas anthropic schedule

# 重启服务
sudo systemctl start ai-trading-bot

# 查看状态
sudo systemctl status ai-trading-bot
```

## 💰 成本估算

**Hostinger VPS 价格（截至 2025）:**
- KVM 1: ~$4-6/月（1核, 2GB RAM）- 适合测试
- KVM 2: ~$8-10/月（2核, 4GB RAM）- 推荐 ⭐
- KVM 4: ~$16-20/月（4核, 8GB RAM）- 多机器人

**额外成本:**
- Anthropic API: 按使用量计费
  - 每次调用约 $0.01-0.03（取决于 prompt 长度）
  - 每 3 分钟一次 = 每天 480 次 ≈ $5-15/天
  - 可以调整 interval 来降低成本

## ✅ 部署检查清单

- [ ] VPS 已购买并可以 SSH 连接
- [ ] 系统已更新
- [ ] Python 3.9+ 已安装
- [ ] 代码已克隆
- [ ] 虚拟环境已创建
- [ ] 依赖已安装
- [ ] config.json 已配置
- [ ] ANTHROPIC_API_KEY 已设置
- [ ] 系统测试通过
- [ ] systemd 服务已创建
- [ ] 服务已启动并设置自启
- [ ] 日志正常输出
- [ ] 防火墙已配置
- [ ] 备份脚本已设置
- [ ] 监控脚本已设置

## 📞 获取帮助

如果遇到问题：
1. 查看日志 `tail -f ~/ai-trading-bot.log`
2. 查看系统日志 `sudo journalctl -u ai-trading-bot -f`
3. 运行测试 `python ai_trading/test_system.py`
4. 检查网络连接
5. 验证 API Keys

## 🎉 完成！

你的 AI 交易机器人现在应该在 Hostinger VPS 上 24/7 运行了！

记得定期检查：
- 机器人状态
- 交易表现
- 日志文件
- 服务器资源使用

**祝交易顺利！** 🚀

