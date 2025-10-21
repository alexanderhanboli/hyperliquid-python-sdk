#!/bin/bash
# 快速部署脚本 - 在已有用户下使用
# 使用方法: bash quick_deploy.sh

set -e

echo "=========================================="
echo "  AI 交易机器人 - 快速部署"
echo "=========================================="
echo ""

# 1. 克隆代码
if [ -d "hyperliquid-python-sdk" ]; then
    echo "📁 更新现有代码..."
    cd hyperliquid-python-sdk
    git pull origin testnet
else
    echo "📥 克隆代码仓库..."
    git clone https://github.com/alexanderhanboli/hyperliquid-python-sdk.git
    cd hyperliquid-python-sdk
    git checkout testnet
fi

# 2. 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "🐍 创建 Python 虚拟环境..."
    python3 -m venv venv
fi

# 3. 安装依赖
echo "📦 安装依赖..."
source venv/bin/activate
pip install --upgrade pip -q
pip install numpy pandas anthropic schedule -q
pip install -e . -q

# 4. 配置
echo ""
echo "⚙️  配置设置"
echo ""

if [ ! -f "examples/config.json" ]; then
    cp examples/config.json.example examples/config.json
    
    echo "请输入 Hyperliquid 配置:"
    read -p "  钱包地址: " WALLET_ADDRESS
    read -sp "  私钥: " PRIVATE_KEY
    echo ""
    
    cat > examples/config.json << EOF
{
  "account_address": "$WALLET_ADDRESS",
  "secret_key": "$PRIVATE_KEY"
}
EOF
    
    chmod 600 examples/config.json
    echo "✅ Hyperliquid 配置已保存"
else
    echo "✅ Hyperliquid 配置已存在"
fi

# 设置 API Key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo ""
    read -sp "输入 Anthropic API Key: " API_KEY
    echo ""
    export ANTHROPIC_API_KEY="$API_KEY"
    
    # 保存到 bashrc
    if ! grep -q "ANTHROPIC_API_KEY" ~/.bashrc; then
        echo "export ANTHROPIC_API_KEY='$API_KEY'" >> ~/.bashrc
    fi
    echo "✅ API Key 已设置"
else
    echo "✅ API Key 已从环境变量加载"
fi

# 5. 运行测试
echo ""
echo "🧪 运行系统测试..."
python ai_trading/test_system.py

# 6. 询问是否创建服务
echo ""
echo "=========================================="
echo "  部署完成！"
echo "=========================================="
echo ""
read -p "是否创建 systemd 服务以 24/7 运行? (y/n): " CREATE_SERVICE

if [ "$CREATE_SERVICE" = "y" ] || [ "$CREATE_SERVICE" = "Y" ]; then
    # 获取配置
    read -p "交易币种 (默认: BTC ETH SOL): " COINS
    COINS=${COINS:-"BTC ETH SOL"}
    
    read -p "交易间隔(分钟, 默认: 3): " INTERVAL
    INTERVAL=${INTERVAL:-3}
    
    USER=$(whoami)
    HOME_DIR=$HOME
    WORK_DIR="$HOME_DIR/hyperliquid-python-sdk"
    
    # 创建服务文件
    sudo tee /etc/systemd/system/ai-trading-bot.service > /dev/null << EOF
[Unit]
Description=AI Trading Bot - Hyperliquid
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$WORK_DIR
Environment="ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY"
ExecStart=$WORK_DIR/venv/bin/python ai_trading/ai_trader_bot.py --coins $COINS --interval $INTERVAL
Restart=always
RestartSec=10

StandardOutput=append:$HOME_DIR/ai-trading-bot.log
StandardError=append:$HOME_DIR/ai-trading-bot-error.log

[Install]
WantedBy=multi-user.target
EOF
    
    # 启动服务
    sudo systemctl daemon-reload
    sudo systemctl enable ai-trading-bot
    sudo systemctl start ai-trading-bot
    
    echo ""
    echo "✅ 服务已创建并启动！"
    echo ""
    echo "管理命令:"
    echo "  查看状态: sudo systemctl status ai-trading-bot"
    echo "  查看日志: tail -f ~/ai-trading-bot.log"
    echo "  停止服务: sudo systemctl stop ai-trading-bot"
    echo "  重启服务: sudo systemctl restart ai-trading-bot"
else
    echo ""
    echo "手动运行命令:"
    echo ""
    echo "  测试模式:"
    echo "  python ai_trading/ai_trader_bot.py --test"
    echo ""
    echo "  正常模式:"
    echo "  python ai_trading/ai_trader_bot.py --coins BTC ETH SOL --interval 3"
    echo ""
    echo "  使用 screen 后台运行:"
    echo "  screen -S trading"
    echo "  python ai_trading/ai_trader_bot.py"
    echo "  (按 Ctrl+A 然后按 D 断开)"
fi

echo ""
echo "📖 更多信息请查看: HOSTINGER_DEPLOYMENT.md"
echo ""

