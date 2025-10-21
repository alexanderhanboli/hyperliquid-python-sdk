#!/bin/bash
# AI 交易机器人快速启动脚本

echo "=========================================="
echo "  AI 交易机器人 - 快速启动"
echo "=========================================="
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python3"
    exit 1
fi

echo "✅ Python3 已安装"

# 检查依赖
echo "📦 检查依赖..."
python3 -c "import anthropic" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️ anthropic 未安装，正在安装..."
    pip install anthropic
fi

python3 -c "import schedule" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️ schedule 未安装，正在安装..."
    pip install schedule
fi

python3 -c "import pandas" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️ pandas 未安装，正在安装..."
    pip install pandas
fi

echo "✅ 依赖检查完成"
echo ""

# 检查 API Key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️ 未设置 ANTHROPIC_API_KEY"
    echo "请运行: export ANTHROPIC_API_KEY='your-api-key'"
    echo ""
    read -p "是否现在输入 API Key? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "请输入 Anthropic API Key: " api_key
        export ANTHROPIC_API_KEY="$api_key"
        echo "✅ API Key 已设置"
    else
        echo "❌ 退出"
        exit 1
    fi
else
    echo "✅ ANTHROPIC_API_KEY 已设置"
fi

echo ""

# 检查配置文件
if [ ! -f "ai_trading/config.json" ]; then
    echo "⚠️ 配置文件不存在，正在创建..."
    cp ai_trading/config.json.example ai_trading/config.json
    echo "✅ 配置文件已创建: ai_trading/config.json"
fi

# 检查 Hyperliquid 配置
if [ ! -f "examples/config.json" ]; then
    echo "⚠️ Hyperliquid 配置文件不存在"
    echo "请先配置 examples/config.json"
    exit 1
else
    echo "✅ Hyperliquid 配置已存在"
fi

echo ""
echo "=========================================="
echo "  启动模式选择"
echo "=========================================="
echo "1. 测试模式 (只运行一次)"
echo "2. 正常模式 (每3分钟运行)"
echo "3. 自定义配置"
echo ""

read -p "请选择 (1/2/3): " choice

case $choice in
    1)
        echo ""
        echo "🧪 测试模式启动..."
        python3 ai_trading/ai_trader_bot.py --test
        ;;
    2)
        echo ""
        echo "🚀 正常模式启动..."
        echo "按 Ctrl+C 停止"
        python3 ai_trading/ai_trader_bot.py
        ;;
    3)
        echo ""
        read -p "交易币种 (空格分隔, 默认: BTC ETH SOL): " coins
        read -p "交易间隔(分钟, 默认: 3): " interval
        
        coins=${coins:-"BTC ETH SOL"}
        interval=${interval:-3}
        
        echo ""
        echo "🚀 自定义模式启动..."
        echo "  币种: $coins"
        echo "  间隔: $interval 分钟"
        echo "按 Ctrl+C 停止"
        python3 ai_trading/ai_trader_bot.py --coins $coins --interval $interval
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

