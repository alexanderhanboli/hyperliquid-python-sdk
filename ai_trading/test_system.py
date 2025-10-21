#!/usr/bin/env python3
"""
系统测试脚本
测试各个模块是否正常工作
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'examples'))

import example_utils
from hyperliquid.utils import constants


def test_imports():
    """测试导入"""
    print("\n" + "="*60)
    print("📦 测试模块导入...")
    print("="*60)
    
    try:
        from market_data import MarketDataFetcher, TechnicalIndicators
        print("✅ market_data 导入成功")
    except Exception as e:
        print(f"❌ market_data 导入失败: {e}")
        return False
    
    try:
        from prompt_builder import PromptBuilder
        print("✅ prompt_builder 导入成功")
    except Exception as e:
        print(f"❌ prompt_builder 导入失败: {e}")
        return False
    
    try:
        from order_executor import OrderExecutor
        print("✅ order_executor 导入成功")
    except Exception as e:
        print(f"❌ order_executor 导入失败: {e}")
        return False
    
    try:
        import anthropic
        print("✅ anthropic 导入成功")
    except Exception as e:
        print(f"❌ anthropic 导入失败: {e}")
        print("   请运行: pip install anthropic")
        return False
    
    try:
        import schedule
        print("✅ schedule 导入成功")
    except Exception as e:
        print(f"❌ schedule 导入失败: {e}")
        print("   请运行: pip install schedule")
        return False
    
    try:
        import pandas
        print("✅ pandas 导入成功")
    except Exception as e:
        print(f"❌ pandas 导入失败: {e}")
        print("   请运行: pip install pandas")
        return False
    
    return True


def test_hyperliquid_connection():
    """测试 Hyperliquid 连接"""
    print("\n" + "="*60)
    print("🔌 测试 Hyperliquid 连接...")
    print("="*60)
    
    try:
        address, info, exchange = example_utils.setup(
            base_url=constants.TESTNET_API_URL,
            skip_ws=True
        )
        print(f"✅ 连接成功")
        print(f"   钱包地址: {address}")
        
        # 测试获取价格
        all_mids = info.all_mids()
        btc_price = all_mids.get("BTC", 0)
        eth_price = all_mids.get("ETH", 0)
        print(f"   BTC 价格: ${float(btc_price):,.2f}")
        print(f"   ETH 价格: ${float(eth_price):,.2f}")
        
        return True, info, exchange
    
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False, None, None


def test_market_data(info):
    """测试市场数据获取"""
    print("\n" + "="*60)
    print("📊 测试市场数据获取...")
    print("="*60)
    
    try:
        from market_data import MarketDataFetcher
        
        fetcher = MarketDataFetcher(info)
        
        # 测试获取价格
        prices = fetcher.get_current_prices(["BTC", "ETH"])
        print(f"✅ 当前价格获取成功:")
        for coin, price in prices.items():
            print(f"   {coin}: ${price:,.2f}")
        
        # 测试获取 K 线
        print("\n📈 测试 K 线数据获取...")
        candles = fetcher.get_candles("BTC", interval="3m", limit=10)
        if candles:
            print(f"✅ K 线数据获取成功 (获取了 {len(candles)} 条)")
            last_candle = candles[-1]
            print(f"   最新K线: 开 ${last_candle['open']:.2f} | "
                  f"高 ${last_candle['high']:.2f} | "
                  f"低 ${last_candle['low']:.2f} | "
                  f"收 ${last_candle['close']:.2f}")
        else:
            print("⚠️ K 线数据为空")
        
        # 测试技术指标计算
        print("\n📐 测试技术指标计算...")
        market_state = fetcher.get_market_state(["BTC"])
        if market_state and "BTC" in market_state:
            btc_data = market_state["BTC"]
            print(f"✅ 技术指标计算成功:")
            print(f"   EMA20: ${btc_data['current_ema20']:,.2f}")
            print(f"   MACD: {btc_data['current_macd']:.3f}")
            print(f"   RSI(7): {btc_data['current_rsi_7']:.2f}")
            print(f"   RSI(14): {btc_data['current_rsi_14']:.2f}")
        else:
            print("⚠️ 市场状态获取失败")
        
        return True
    
    except Exception as e:
        print(f"❌ 市场数据测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_prompt_builder():
    """测试 Prompt 构建"""
    print("\n" + "="*60)
    print("🧠 测试 Prompt 构建...")
    print("="*60)
    
    try:
        from prompt_builder import PromptBuilder
        
        builder = PromptBuilder(coins=["BTC", "ETH"])
        
        # 模拟数据
        market_state = {
            "BTC": {
                "current_price": 107798.5,
                "current_ema20": 107919.353,
                "current_macd": 15.822,
                "current_rsi_7": 29.336,
                "current_rsi_14": 44.075,
                "mid_prices": [107979.0, 108000.0],
                "ema20_series": [107878.406, 107891.891],
                "macd_series": [52.408, 55.997],
                "rsi7_series": [62.512, 63.321],
                "rsi14_series": [61.14, 61.542],
                "current_volume": 151.082,
                "avg_volume": 4897.702,
            }
        }
        
        account_info = {
            "total_return_pct": 11.88,
            "available_cash": 4927.64,
            "total_value": 11187.63,
        }
        
        prompt = builder.build_prompt(market_state, account_info, [])
        
        print(f"✅ Prompt 构建成功")
        print(f"   Prompt 长度: {len(prompt)} 字符")
        print(f"   包含 'BTC' 次数: {prompt.count('BTC')}")
        
        # 保存到文件
        with open("ai_trading/test_prompt.txt", "w") as f:
            f.write(prompt)
        print(f"   已保存到: ai_trading/test_prompt.txt")
        
        return True
    
    except Exception as e:
        print(f"❌ Prompt 构建测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_anthropic_api():
    """测试 Anthropic API"""
    print("\n" + "="*60)
    print("🤖 测试 Anthropic API...")
    print("="*60)
    
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    if not api_key:
        print("⚠️ 未设置 ANTHROPIC_API_KEY，跳过测试")
        print("   设置方法: export ANTHROPIC_API_KEY='your-api-key'")
        return True  # 不算失败
    
    try:
        import anthropic
        
        client = anthropic.Anthropic(api_key=api_key)
        
        # 简单测试
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=100,
            messages=[
                {"role": "user", "content": "Say 'API test successful' in JSON format"}
            ]
        )
        
        response = message.content[0].text
        print(f"✅ Anthropic API 连接成功")
        print(f"   响应: {response[:100]}...")
        
        return True
    
    except Exception as e:
        print(f"❌ Anthropic API 测试失败: {e}")
        return False


def main():
    """主函数"""
    print("\n" + "="*80)
    print("  🧪 AI 交易机器人系统测试")
    print("="*80)
    
    results = []
    
    # 1. 测试导入
    results.append(("模块导入", test_imports()))
    
    if not results[-1][1]:
        print("\n❌ 基础模块导入失败，请先安装依赖")
        return
    
    # 2. 测试 Hyperliquid 连接
    success, info, exchange = test_hyperliquid_connection()
    results.append(("Hyperliquid 连接", success))
    
    if not success:
        print("\n❌ Hyperliquid 连接失败，请检查配置")
        return
    
    # 3. 测试市场数据
    results.append(("市场数据获取", test_market_data(info)))
    
    # 4. 测试 Prompt 构建
    results.append(("Prompt 构建", test_prompt_builder()))
    
    # 5. 测试 Anthropic API
    results.append(("Anthropic API", test_anthropic_api()))
    
    # 总结
    print("\n" + "="*80)
    print("  📋 测试总结")
    print("="*80)
    
    for name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {name}")
    
    all_passed = all(r[1] for r in results)
    
    if all_passed:
        print("\n🎉 所有测试通过！系统已准备就绪！")
        print("\n下一步:")
        print("  1. 设置 ANTHROPIC_API_KEY (如果还未设置)")
        print("  2. 运行测试模式: python ai_trading/ai_trader_bot.py --test")
        print("  3. 运行正常模式: python ai_trading/ai_trader_bot.py")
    else:
        print("\n⚠️ 部分测试失败，请检查相关配置")
    
    print("="*80 + "\n")


if __name__ == "__main__":
    main()

