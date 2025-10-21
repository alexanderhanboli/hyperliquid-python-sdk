#!/usr/bin/env python3
"""
订单类型实践脚本
安全地测试限价单、市价单、止损止盈
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'examples'))

import example_utils
from hyperliquid.utils import constants

def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def example_1_limit_order(info, exchange, address):
    """示例 1: 限价单"""
    print_header("📝 示例 1: 限价单 (Limit Order)")
    
    # 获取当前价格
    all_mids = info.all_mids()
    current_price = float(all_mids["ETH"])
    print(f"当前 ETH 价格: ${current_price:.2f}")
    
    # 设置一个不会成交的低价
    test_price = int(current_price * 0.7)  # 当前价的 70%
    test_size = 0.01
    
    print(f"\n我们将下一个买入限价单:")
    print(f"  币种: ETH")
    print(f"  方向: 买入 (is_buy=True)")
    print(f"  数量: {test_size} ETH")
    print(f"  限价: ${test_price} (远低于市场价，不会成交)")
    print(f"  类型: 限价单 GTC (Good Till Cancel)")
    
    input("\n按回车继续下单...")
    
    # 下限价单
    result = exchange.order(
        name="ETH",
        is_buy=True,
        sz=test_size,
        limit_px=test_price,
        order_type={"limit": {"tif": "Gtc"}},
        reduce_only=False
    )
    
    if result["status"] == "ok":
        oid = result["response"]["data"]["statuses"][0]["resting"]["oid"]
        print(f"✅ 订单创建成功! 订单ID: {oid}")
        print(f"   订单会一直挂在订单簿上，直到:")
        print(f"   - ETH 价格跌到 ${test_price} 或以下")
        print(f"   - 你手动取消订单")
        
        input("\n按回车取消订单...")
        
        # 取消订单
        cancel_result = exchange.cancel("ETH", oid)
        if cancel_result["status"] == "ok":
            print("✅ 订单已取消")
    else:
        print(f"❌ 订单失败: {result}")
    
    print("\n💡 学到的知识:")
    print("   - 限价单可以精确控制价格")
    print("   - GTC 订单会一直有效直到成交或取消")
    print("   - 适合不着急成交，想要好价格的场景")

def example_2_market_order_simulation(info, exchange, address):
    """示例 2: 市价单模拟（不实际成交）"""
    print_header("⚡ 示例 2: 市价单原理 (不实际下单)")
    
    all_mids = info.all_mids()
    current_price = float(all_mids["ETH"])
    test_size = 0.01
    
    print(f"当前 ETH 价格: ${current_price:.2f}")
    print(f"\n如果我们要市价买入 {test_size} ETH:")
    
    # 模拟市价单逻辑
    slippage = 0.05  # 5% 滑点容忍
    aggressive_price = current_price * (1 + slippage)
    
    print(f"\n市价单的实现原理:")
    print(f"  1. 获取当前价格: ${current_price:.2f}")
    print(f"  2. 加上滑点容忍 ({slippage*100}%): ${aggressive_price:.2f}")
    print(f"  3. 以 IoC (立即成交或取消) 模式下限价单")
    print(f"  4. 订单会立即以最优价格成交")
    
    print(f"\n这样做的好处:")
    print(f"  ✅ 确保立即成交")
    print(f"  ✅ 有滑点保护（不会超过 {slippage*100}%）")
    print(f"  ✅ 比纯市价单更安全")
    
    print(f"\n代码实现:")
    print(f"""
    exchange.market_open(
        coin="ETH",
        is_buy=True,
        sz={test_size},
        slippage={slippage}
    )
    """)
    
    print("\n💡 学到的知识:")
    print("   - 市价单 = 激进限价 + IoC 模式")
    print("   - 适合需要立即成交的场景")
    print("   - 滑点参数很重要，保护你不被割")

def example_3_stop_loss(info, exchange, address):
    """示例 3: 止损单"""
    print_header("🛡️ 示例 3: 止损单 (Stop Loss)")
    
    all_mids = info.all_mids()
    current_price = float(all_mids["ETH"])
    
    print("假设场景:")
    print(f"  你以 ${current_price:.2f} 买入了 0.1 ETH (做多)")
    print(f"  你希望如果价格跌到 {-5}%，自动止损")
    
    entry_price = current_price
    position_size = 0.01  # 使用小额测试
    stop_loss_price = entry_price * 0.95  # -5% 止损
    
    print(f"\n止损单参数:")
    print(f"  入场价: ${entry_price:.2f}")
    print(f"  止损价: ${stop_loss_price:.2f}")
    print(f"  最大亏损: ${(stop_loss_price - entry_price) * position_size:.2f}")
    print(f"  风险百分比: -5%")
    
    print(f"\n我们将创建一个止损单:")
    input("按回车创建止损单...")
    
    result = exchange.order(
        name="ETH",
        is_buy=False,           # 止损是卖出
        sz=position_size,
        limit_px=stop_loss_price * 0.98,  # 稍低于触发价
        order_type={
            "trigger": {
                "triggerPx": stop_loss_price,
                "isMarket": True,
                "tpsl": "sl"
            }
        },
        reduce_only=True        # ⚠️ 只减仓！
    )
    
    if result["status"] == "ok":
        status = result["response"]["data"]["statuses"][0]
        if "resting" in status:
            oid = status["resting"]["oid"]
            print(f"✅ 止损单已创建! 订单ID: {oid}")
            print(f"\n止损单工作原理:")
            print(f"  1. 价格正常时，订单挂单等待")
            print(f"  2. 当价格跌到 ${stop_loss_price:.2f}，触发止损")
            print(f"  3. 立即以市价卖出 {position_size} ETH")
            print(f"  4. 锁定损失在 -5% 以内")
            
            input("\n按回车取消止损单...")
            cancel_result = exchange.cancel("ETH", oid)
            if cancel_result["status"] == "ok":
                print("✅ 止损单已取消")
        else:
            print(f"⚠️ 订单响应: {status}")
            if "error" in status:
                print(f"   错误: {status['error']}")
    else:
        print(f"❌ 创建失败: {result}")
    
    print("\n💡 学到的知识:")
    print("   - 止损单是条件订单，达到触发价才执行")
    print("   - reduce_only=True 确保只平仓，不反向开仓")
    print("   - isMarket=True 确保触发后立即成交")
    print("   - 止损是风险管理的核心工具")

def example_4_take_profit(info, exchange, address):
    """示例 4: 止盈单"""
    print_header("💰 示例 4: 止盈单 (Take Profit)")
    
    all_mids = info.all_mids()
    current_price = float(all_mids["ETH"])
    
    print("假设场景:")
    print(f"  你以 ${current_price:.2f} 买入了 0.1 ETH (做多)")
    print(f"  你希望如果价格涨到 {+8}%，自动止盈")
    
    entry_price = current_price
    position_size = 0.01
    take_profit_price = entry_price * 1.08  # +8% 止盈
    
    print(f"\n止盈单参数:")
    print(f"  入场价: ${entry_price:.2f}")
    print(f"  止盈价: ${take_profit_price:.2f}")
    print(f"  预期利润: ${(take_profit_price - entry_price) * position_size:.2f}")
    print(f"  收益百分比: +8%")
    
    print(f"\n我们将创建一个止盈单:")
    input("按回车创建止盈单...")
    
    result = exchange.order(
        name="ETH",
        is_buy=False,           # 止盈是卖出
        sz=position_size,
        limit_px=take_profit_price * 1.02,  # 稍高于触发价
        order_type={
            "trigger": {
                "triggerPx": take_profit_price,
                "isMarket": True,
                "tpsl": "tp"
            }
        },
        reduce_only=True
    )
    
    if result["status"] == "ok":
        status = result["response"]["data"]["statuses"][0]
        if "resting" in status:
            oid = status["resting"]["oid"]
            print(f"✅ 止盈单已创建! 订单ID: {oid}")
            print(f"\n止盈单工作原理:")
            print(f"  1. 价格正常时，订单挂单等待")
            print(f"  2. 当价格涨到 ${take_profit_price:.2f}，触发止盈")
            print(f"  3. 立即以市价卖出 {position_size} ETH")
            print(f"  4. 锁定利润在 +8%")
            
            input("\n按回车取消止盈单...")
            cancel_result = exchange.cancel("ETH", oid)
            if cancel_result["status"] == "ok":
                print("✅ 止盈单已取消")
        else:
            print(f"⚠️ 订单响应: {status}")
            if "error" in status:
                print(f"   错误: {status['error']}")
            print(f"\n   ℹ️ 注意: 止损/止盈单需要先有对应的持仓才能创建")
    else:
        print(f"❌ 创建失败: {result}")
    
    print("\n💡 学到的知识:")
    print("   - 止盈单与止损单原理相同，只是方向相反")
    print("   - 自动锁定利润，避免贪婪")
    print("   - 通常与止损一起使用，形成完整策略")

def example_5_complete_strategy(info, exchange, address):
    """示例 5: 完整交易策略"""
    print_header("🎯 示例 5: 完整交易策略")
    
    all_mids = info.all_mids()
    current_price = float(all_mids["ETH"])
    
    print("一个完整的交易应该包含:")
    print("  1. 入场订单")
    print("  2. 止损订单 (保护资金)")
    print("  3. 止盈订单 (锁定利润)")
    
    # 策略参数
    entry_price = current_price * 0.98  # 稍低价格入场
    position_size = 0.01
    stop_loss_price = entry_price * 0.95  # -5% 止损
    take_profit_price = entry_price * 1.10  # +10% 止盈
    
    risk = (entry_price - stop_loss_price) * position_size
    reward = (take_profit_price - entry_price) * position_size
    risk_reward_ratio = reward / risk if risk > 0 else 0
    
    print(f"\n策略参数:")
    print(f"  当前价格: ${current_price:.2f}")
    print(f"  入场价格: ${entry_price:.2f}")
    print(f"  仓位大小: {position_size} ETH")
    print(f"  止损价格: ${stop_loss_price:.2f} (-5%)")
    print(f"  止盈价格: ${take_profit_price:.2f} (+10%)")
    print(f"\n风险分析:")
    print(f"  最大风险: ${risk:.2f}")
    print(f"  预期收益: ${reward:.2f}")
    print(f"  风险收益比: 1:{risk_reward_ratio:.1f}")
    
    if risk_reward_ratio >= 2:
        print(f"  ✅ 风险收益比良好 (>= 1:2)")
    else:
        print(f"  ⚠️ 风险收益比偏低 (< 1:2)")
    
    print("\n这就是一个完整的交易计划!")
    print("在实际交易中，你需要:")
    print("  1. 先下入场单")
    print("  2. 成交后立即设置止损")
    print("  3. 同时设置止盈")
    print("  4. 让系统自动管理风险")
    
    print("\n💡 学到的知识:")
    print("   - 永远不要没有止损就交易")
    print("   - 风险收益比至少要 1:2")
    print("   - 让系统自动执行，避免情绪干扰")
    print("   - 这是专业交易者的基本功")

def main():
    print("=" * 70)
    print("  🎓 Hyperliquid 订单类型实践教程")
    print("=" * 70)
    print("\n这个脚本会带你逐步学习:")
    print("  1. 限价单 - 如何精确控制价格")
    print("  2. 市价单 - 如何立即成交")
    print("  3. 止损单 - 如何保护资金")
    print("  4. 止盈单 - 如何锁定利润")
    print("  5. 完整策略 - 如何组合使用")
    
    print("\n所有测试都使用:")
    print("  ✅ 测试网 (不会损失真实资金)")
    print("  ✅ 小额测试 (0.01 ETH)")
    print("  ✅ 不会实际成交的价格")
    print("  ✅ 每个订单都会被取消")
    
    input("\n准备好了吗？按回车开始...")
    
    # 初始化
    address, info, exchange = example_utils.setup(
        base_url=constants.TESTNET_API_URL,
        skip_ws=True
    )
    
    # 运行示例
    example_1_limit_order(info, exchange, address)
    example_2_market_order_simulation(info, exchange, address)
    example_3_stop_loss(info, exchange, address)
    example_4_take_profit(info, exchange, address)
    example_5_complete_strategy(info, exchange, address)
    
    # 总结
    print("\n" + "=" * 70)
    print("  🎉 恭喜！你已经掌握了所有基本订单类型！")
    print("=" * 70)
    print("\n下一步:")
    print("  1. 阅读 ORDER_TYPES_GUIDE.md 了解更多细节")
    print("  2. 查看 examples/ 目录中的其他示例")
    print("  3. 在测试网充分练习")
    print("  4. 准备好后再考虑实盘交易")
    print("\n记住：风险管理永远是第一位的！")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()

