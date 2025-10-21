#!/bin/bash
# DeepSeek AI 交易机器人启动脚本

# 设置 DeepSeek API Key
export DEEPSEEK_API_KEY='sk-b14ed35ef1564874952a45ff819f2f7a'

# 激活虚拟环境
cd "$(dirname "$0")/.."
source venv/bin/activate

echo "================================================"
echo "  🤖 DeepSeek AI 交易机器人"
echo "================================================"
echo ""
echo "模型: deepseek-reasoner (思考模式)"
echo "价格: \$0.28/M 输入 tokens, \$0.42/M 输出 tokens"
echo ""
echo "================================================"
echo ""

# 运行交易机器人
python ai_trading/ai_trader_bot.py \
    --model deepseek-reasoner \
    --coins BTC ETH SOL \
    --interval 3 \
    --testnet \
    "$@"

