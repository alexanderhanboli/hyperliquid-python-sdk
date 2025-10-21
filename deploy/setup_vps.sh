#!/bin/bash
# Hostinger VPS 自动部署脚本
# 使用方法: bash setup_vps.sh

set -e  # 遇到错误立即退出

echo "=========================================="
echo "  AI 交易机器人 - VPS 自动部署"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否为 root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}请使用 root 用户运行此脚本${NC}"
    echo "使用: sudo bash setup_vps.sh"
    exit 1
fi

echo -e "${GREEN}步骤 1/6: 更新系统...${NC}"
apt update && apt upgrade -y

echo ""
echo -e "${GREEN}步骤 2/6: 安装必要软件...${NC}"
apt install -y python3 python3-pip python3-venv git curl wget nano htop

echo ""
echo -e "${GREEN}步骤 3/6: 创建非 root 用户...${NC}"
read -p "输入新用户名 (默认: trader): " USERNAME
USERNAME=${USERNAME:-trader}

if id "$USERNAME" &>/dev/null; then
    echo -e "${YELLOW}用户 $USERNAME 已存在，跳过创建${NC}"
else
    adduser --gecos "" $USERNAME
    usermod -aG sudo $USERNAME
    echo -e "${GREEN}用户 $USERNAME 创建成功${NC}"
fi

echo ""
echo -e "${GREEN}步骤 4/6: 设置防火墙...${NC}"
apt install -y ufw
ufw --force enable
ufw allow 22/tcp
echo -e "${GREEN}防火墙已启用，SSH 端口已开放${NC}"

echo ""
echo -e "${GREEN}步骤 5/6: 安装 Python 依赖...${NC}"
pip3 install --upgrade pip

echo ""
echo -e "${GREEN}步骤 6/6: 创建部署脚本...${NC}"

# 为新用户创建部署脚本
cat > /home/$USERNAME/deploy_bot.sh << 'DEPLOY_SCRIPT'
#!/bin/bash

set -e

echo "=========================================="
echo "  部署 AI 交易机器人"
echo "=========================================="
echo ""

# 克隆代码
if [ -d "hyperliquid-python-sdk" ]; then
    echo "代码目录已存在，更新代码..."
    cd hyperliquid-python-sdk
    git pull origin testnet
    cd ~
else
    echo "克隆代码..."
    git clone https://github.com/alexanderhanboli/hyperliquid-python-sdk.git
    cd hyperliquid-python-sdk
    git checkout testnet
    cd ~
fi

# 创建虚拟环境
cd hyperliquid-python-sdk
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境并安装依赖
echo "安装依赖..."
source venv/bin/activate
pip install --upgrade pip
pip install numpy pandas anthropic schedule
pip install -e .

# 配置文件
if [ ! -f "examples/config.json" ]; then
    echo ""
    echo "配置 Hyperliquid 钱包..."
    cp examples/config.json.example examples/config.json
    
    read -p "输入钱包地址: " WALLET_ADDRESS
    read -p "输入私钥: " PRIVATE_KEY
    
    cat > examples/config.json << EOF
{
  "account_address": "$WALLET_ADDRESS",
  "secret_key": "$PRIVATE_KEY"
}
EOF
    
    chmod 600 examples/config.json
    echo "配置文件已创建"
else
    echo "配置文件已存在"
fi

# 设置环境变量
if ! grep -q "ANTHROPIC_API_KEY" ~/.bashrc; then
    echo ""
    read -p "输入 Anthropic API Key: " API_KEY
    echo "export ANTHROPIC_API_KEY='$API_KEY'" >> ~/.bashrc
    source ~/.bashrc
    echo "API Key 已设置"
fi

# 运行测试
echo ""
echo "运行系统测试..."
python ai_trading/test_system.py

echo ""
echo "=========================================="
echo "  部署完成！"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 测试运行: python ai_trading/ai_trader_bot.py --test"
echo "2. 创建服务: sudo bash ~/create_service.sh"
echo ""

DEPLOY_SCRIPT

chmod +x /home/$USERNAME/deploy_bot.sh
chown $USERNAME:$USERNAME /home/$USERNAME/deploy_bot.sh

# 创建服务脚本
cat > /home/$USERNAME/create_service.sh << 'SERVICE_SCRIPT'
#!/bin/bash

if [ "$EUID" -ne 0 ]; then 
    echo "请使用 sudo 运行此脚本"
    exit 1
fi

USER=$(logname)
HOME_DIR=$(eval echo ~$USER)

echo "创建 systemd 服务..."

# 获取配置
read -p "交易币种 (默认: BTC ETH SOL): " COINS
COINS=${COINS:-"BTC ETH SOL"}

read -p "交易间隔(分钟, 默认: 3): " INTERVAL
INTERVAL=${INTERVAL:-3}

read -p "Anthropic API Key: " API_KEY

# 创建服务文件
cat > /etc/systemd/system/ai-trading-bot.service << EOF
[Unit]
Description=AI Trading Bot - Hyperliquid
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME_DIR/hyperliquid-python-sdk
Environment="ANTHROPIC_API_KEY=$API_KEY"
ExecStart=$HOME_DIR/hyperliquid-python-sdk/venv/bin/python ai_trading/ai_trader_bot.py --coins $COINS --interval $INTERVAL
Restart=always
RestartSec=10

StandardOutput=append:$HOME_DIR/ai-trading-bot.log
StandardError=append:$HOME_DIR/ai-trading-bot-error.log

[Install]
WantedBy=multi-user.target
EOF

# 重新加载并启动
systemctl daemon-reload
systemctl enable ai-trading-bot
systemctl start ai-trading-bot

echo ""
echo "服务已创建并启动！"
echo ""
echo "管理命令:"
echo "  查看状态: sudo systemctl status ai-trading-bot"
echo "  查看日志: tail -f ~/ai-trading-bot.log"
echo "  停止服务: sudo systemctl stop ai-trading-bot"
echo "  重启服务: sudo systemctl restart ai-trading-bot"
echo ""

SERVICE_SCRIPT

chmod +x /home/$USERNAME/create_service.sh
chown $USERNAME:$USERNAME /home/$USERNAME/create_service.sh

# 创建监控脚本
cat > /home/$USERNAME/monitor_bot.sh << 'MONITOR_SCRIPT'
#!/bin/bash

echo "=========================================="
echo "  AI 交易机器人监控"
echo "=========================================="
echo ""

echo "服务状态:"
sudo systemctl is-active ai-trading-bot 2>/dev/null || echo "未运行"
echo ""

echo "最近 10 行日志:"
tail -n 10 ~/ai-trading-bot.log 2>/dev/null || echo "无日志"
echo ""

echo "内存使用:"
ps aux | grep ai_trader_bot.py | grep -v grep || echo "进程未找到"
echo ""

echo "磁盘使用:"
df -h | grep -E '^/dev/'
echo ""

MONITOR_SCRIPT

chmod +x /home/$USERNAME/monitor_bot.sh
chown $USERNAME:$USERNAME /home/$USERNAME/monitor_bot.sh

echo ""
echo -e "${GREEN}=========================================="
echo "  安装完成！"
echo "==========================================${NC}"
echo ""
echo "下一步："
echo "1. 切换到新用户: su - $USERNAME"
echo "2. 运行部署脚本: ./deploy_bot.sh"
echo "3. 创建服务: sudo ./create_service.sh"
echo "4. 监控机器人: ./monitor_bot.sh"
echo ""
echo -e "${YELLOW}重要提示：${NC}"
echo "- 配置文件将保存在 ~/hyperliquid-python-sdk/examples/config.json"
echo "- 确保妥善保管私钥和 API Keys"
echo "- 建议先在测试网运行和测试"
echo ""
echo "详细文档: HOSTINGER_DEPLOYMENT.md"
echo ""

