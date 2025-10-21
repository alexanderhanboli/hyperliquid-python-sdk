#!/usr/bin/env python3
"""
AI 交易机器人演示脚本
展示如何使用 AI 交易系统
"""

import sys
import os

print("""
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║       🤖 AI 交易机器人 - 复现 nof1.ai 架构                      ║
║                                                                ║
║       基于 Claude Sonnet 4.5 的自动交易系统                     ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝

这个演示将展示如何：
  1. 获取市场数据和计算技术指标
  2. 构建给 AI 的 prompt
  3. （可选）调用 AI 获取决策
  4. 执行交易订单

⚠️  注意：默认使用测试网，不会使用真实资金

""")

input("按回车继续...")

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'examples'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai_trading'))

import example_utils
from hyperliquid.utils import constants
from market_data import MarketDataFetcher
from prompt_builder import PromptBuilder
from order_executor import OrderExecutor

def demo_step_1():
    """步骤 1: 连接到 Hyperliquid"""
    print("\n" + "="*70)
    print("步骤 1: 连接到 Hyperliquid (测试网)")
    print("="*70)
    
    address, info, exchange = example_utils.setup(
        base_url=constants.TESTNET_API_URL,
        skip_ws=True
    )
    
    print(f"✅ 连接成功！")
    print(f"   钱包地址: {address}")
    
    return address, info, exchange

def demo_step_2(info):
    """步骤 2: 获取市场数据"""
    print("\n" + "="*70)
    print("步骤 2: 获取市场数据和技术指标")
    print("="*70)
    
    coins = ["BTC", "ETH", "SOL"]
    fetcher = MarketDataFetcher(info)
    
    print(f"\n正在获取 {', '.join(coins)} 的市场数据...")
    
    # 获取当前价格
    prices = fetcher.get_current_prices(coins)
    print("\n📊 当前价格:")
    for coin, price in prices.items():
        print(f"   {coin}: ${price:,.2f}")
    
    # 获取完整市场状态（包含技术指标）
    print("\n⏳ 计算技术指标...")
    market_state = fetcher.get_market_state(coins)
    
    print("\n📈 技术指标 (以 BTC 为例):")
    if "BTC" in market_state:
        btc = market_state["BTC"]
        print(f"   当前价格: ${btc['current_price']:,.2f}")
        print(f"   EMA(20): ${btc['current_ema20']:,.2f}")
        print(f"   MACD: {btc['current_macd']:.3f}")
        print(f"   RSI(7): {btc['current_rsi_7']:.2f}")
        print(f"   RSI(14): {btc['current_rsi_14']:.2f}")
        
        # RSI 解读
        rsi = btc['current_rsi_14']
        if rsi < 30:
            print(f"   👉 RSI < 30: 超卖，可能反弹")
        elif rsi > 70:
            print(f"   👉 RSI > 70: 超买，可能回调")
        else:
            print(f"   👉 RSI 正常范围")
    
    return market_state

def demo_step_3(market_state, info, exchange):
    """步骤 3: 构建 AI Prompt"""
    print("\n" + "="*70)
    print("步骤 3: 构建 AI Prompt")
    print("="*70)
    
    # 获取账户信息
    executor = OrderExecutor(exchange, info)
    account_info = executor.get_account_value()
    positions = executor.get_current_positions()
    
    # 添加收益率信息
    initial_capital = 10000.0
    account_info['total_return_pct'] = 0.0  # 演示用
    
    print(f"\n💰 账户信息:")
    print(f"   总价值: ${account_info['total_value']:.2f}")
    print(f"   可用资金: ${account_info['available_cash']:.2f}")
    print(f"   持仓数量: {len(positions)}")
    
    # 构建 prompt
    builder = PromptBuilder(coins=["BTC", "ETH", "SOL"])
    prompt = builder.build_prompt(
        market_state=market_state,
        account_info=account_info,
        positions=positions
    )
    
    print(f"\n📝 Prompt 已构建:")
    print(f"   总长度: {len(prompt)} 字符")
    print(f"   包含的数据:")
    print(f"     - 市场数据和技术指标")
    print(f"     - 账户状态和持仓")
    print(f"     - 交易指令和规则")
    
    # 保存到文件
    with open("ai_trading/demo_prompt.txt", "w") as f:
        f.write(prompt)
    
    print(f"\n   已保存到: ai_trading/demo_prompt.txt")
    print(f"\n   Prompt 预览 (前 500 字符):")
    print("   " + "-"*66)
    print("   " + prompt[:500].replace("\n", "\n   "))
    print("   " + "-"*66)
    
    return prompt

def demo_step_4():
    """步骤 4: AI 决策示例"""
    print("\n" + "="*70)
    print("步骤 4: AI 决策示例 (模拟)")
    print("="*70)
    
    print("""
在实际使用中，AI (Claude Sonnet 4.5) 会分析 prompt 并返回 JSON 格式的决策。

示例决策 1: 开多仓 BTC
{
  "BTC": {
    "trade_signal_args": {
      "coin": "BTC",
      "signal": "entry",
      "is_buy": true,
      "quantity": 0.1,
      "profit_target": 115000,
      "stop_loss": 105000,
      "leverage": 10,
      "confidence": 0.75,
      "justification": "RSI 显示超卖在 28，MACD 出现看涨背离，
                       价格跌破 EMA20 后开始反弹，风险收益比 1:2.5"
    }
  }
}

如果这个决策被执行，机器人会：
  1. ✅ 设置 10x 杠杆
  2. ✅ 市价买入 0.1 BTC
  3. ✅ 设置止盈单在 $115,000
  4. ✅ 设置止损单在 $105,000

风险分析:
  - 入场: ~$108,000
  - 止损: $105,000 (-2.8%)
  - 止盈: $115,000 (+6.5%)
  - 风险收益比: 1:2.3 ✅
  - 最大风险: $300 (0.1 BTC × $3,000 价差)
  - 预期收益: $700 (0.1 BTC × $7,000 价差)
""")

def demo_step_5():
    """步骤 5: 如何运行"""
    print("\n" + "="*70)
    print("步骤 5: 如何运行 AI 交易机器人")
    print("="*70)
    
    print("""
要运行完整的 AI 交易机器人，你需要:

1. 设置 Anthropic API Key:
   export ANTHROPIC_API_KEY='your-api-key'
   
   获取 API Key: https://console.anthropic.com/

2. 测试模式（只运行一次）:
   python ai_trading/ai_trader_bot.py --test

3. 正常模式（每 3 分钟自动运行）:
   python ai_trading/ai_trader_bot.py

4. 自定义配置:
   python ai_trading/ai_trader_bot.py --coins BTC ETH --interval 5

运行时，机器人会:
  ⏰ 每 N 分钟自动执行一次交易循环
  📊 获取最新市场数据
  🧠 调用 Claude AI 分析
  ⚡ 执行 AI 的交易决策
  💾 记录 prompt 和决策到文件

查看结果:
  - AI 的 prompt: ai_trading/last_prompt.txt
  - AI 的决策: ai_trading/last_decision.json
  - 终端会显示详细的执行日志
""")

def main():
    """主函数"""
    try:
        # 步骤 1: 连接
        address, info, exchange = demo_step_1()
        input("\n按回车继续到步骤 2...")
        
        # 步骤 2: 获取市场数据
        market_state = demo_step_2(info)
        input("\n按回车继续到步骤 3...")
        
        # 步骤 3: 构建 prompt
        prompt = demo_step_3(market_state, info, exchange)
        input("\n按回车继续到步骤 4...")
        
        # 步骤 4: AI 决策示例
        demo_step_4()
        input("\n按回车继续到步骤 5...")
        
        # 步骤 5: 如何运行
        demo_step_5()
        
        print("\n" + "="*70)
        print("🎉 演示完成！")
        print("="*70)
        print("""
下一步:
  1. 阅读 AI_TRADING_GUIDE.md 了解详细信息
  2. 运行系统测试: python ai_trading/test_system.py
  3. 设置 ANTHROPIC_API_KEY
  4. 测试运行: python ai_trading/ai_trader_bot.py --test

相关文档:
  - AI_TRADING_GUIDE.md - 完整使用指南
  - ai_trading/README.md - 系统架构说明
  - ORDER_TYPES_GUIDE.md - 订单类型详解

⚠️  记住: 先在测试网充分练习，再考虑真实交易！
""")
        print("="*70 + "\n")
        
    except KeyboardInterrupt:
        print("\n\n👋 演示已取消")
    except Exception as e:
        print(f"\n❌ 演示出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

