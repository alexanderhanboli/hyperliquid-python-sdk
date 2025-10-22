#!/bin/bash
# DeepSeek AI 交易机器人启动脚本

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Python 会通过 python-dotenv 自动加载 .env 文件
# 这里只做友好提示
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo "⚠️ 提示: 未找到 .env 配置文件"
    echo ""
    echo "首次使用请创建配置文件:"
    echo "  cd $SCRIPT_DIR"
    echo "  cp .env.example .env"
    echo "  nano .env  # 编辑并填入你的 API Key"
    echo ""
    read -p "是否继续运行? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 激活虚拟环境（如果存在）
cd "$(dirname "$0")/.."
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "================================================"
echo "  🤖 DeepSeek AI 交易机器人"
echo "================================================"
echo ""
echo "模型: deepseek-reasoner (思考模式)"
echo "价格: \$0.28/M 输入 tokens, \$0.42/M 输出 tokens"
echo ""
echo "================================================"
echo ""
echo "使用示例:"
echo "  ./start_deepseek.sh                      # 使用默认币种 BTC ETH SOL"
echo "  ./start_deepseek.sh --top-coins 20       # 交易市值前20名的币种"
echo "  ./start_deepseek.sh --coins BTC ETH      # 指定特定币种"
echo ""

# 运行交易机器人
if [ $# -eq 0 ]; then
    # 默认参数：使用BTC ETH SOL
    python ai_trading/ai_trader_bot.py \
        --model deepseek-reasoner \
        --coins BTC ETH SOL \
        --interval 3 \
        --testnet
else
    # 使用用户指定的参数
    python ai_trading/ai_trader_bot.py \
        --model deepseek-reasoner \
        --interval 3 \
        --testnet \
        "$@"
fi

