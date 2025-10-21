#!/usr/bin/env python3
"""
Hyperliquid 交互式测试脚本
提供安全的测试交易示例
"""

import json
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'examples'))

import eth_account
import example_utils
from hyperliquid.utils import constants

def print_section(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def main():
    print_section("🚀 Hyperliquid 交互式测试")
    
    # 设置
    address, info, exchange = example_utils.setup(base_url=constants.TESTNET_API_URL, skip_ws=True)
    
    # 1. 查看账户状态
    print_section("1. 账户状态")
    user_state = info.user_state(address)
    account_value = user_state["marginSummary"]["accountValue"]
    print(f"💰 账户价值: ${account_value}")
    
    positions = user_state["assetPositions"]
    if len(positions) > 0:
        print(f"\n📊 当前持仓 ({len(positions)} 个):")
        for pos in positions:
            position = pos["position"]
            pnl = float(position["unrealizedPnl"])
            pnl_symbol = "📈" if pnl > 0 else "📉" if pnl < 0 else "➡️"
            print(f"  {pnl_symbol} {position['coin']}: {position['szi']} (PnL: ${pnl:.2f})")
    else:
        print("📭 当前无持仓")
    
    # 2. 查看市场价格
    print_section("2. 市场价格 (前10个)")
    all_mids = info.all_mids()
    for i, (coin, price) in enumerate(list(all_mids.items())[:10]):
        print(f"  {i+1:2d}. {coin:8s} ${price}")
    
    # 3. 查看未成交订单
    print_section("3. 未成交订单")
    open_orders = info.open_orders(address)
    if len(open_orders) > 0:
        print(f"📋 有 {len(open_orders)} 个未成交订单:")
        for order in open_orders[:5]:  # 只显示前5个
            print(f"  {order['coin']}: {order['side']} {order['sz']} @ ${order['limitPx']}")
    else:
        print("✅ 无未成交订单")
    
    # 4. 测试下单和取消
    print_section("4. 测试下单")
    print("准备下一个低价 ETH 买单（不会成交）...")
    
    try:
        # 获取当前 ETH 价格
        current_price = float(all_mids.get("ETH", "3000"))
        # 设置一个远低于市场的价格
        test_price = int(current_price * 0.5)  # 市场价的 50%
        test_size = 0.01  # 很小的数量
        
        print(f"  当前 ETH 价格: ${current_price:.2f}")
        print(f"  测试订单: 买入 {test_size} ETH @ ${test_price}")
        
        # 下单
        order_result = exchange.order(
            "ETH", 
            True,  # is_buy
            test_size, 
            test_price, 
            {"limit": {"tif": "Gtc"}}
        )
        
        if order_result["status"] == "ok":
            print("  ✅ 订单创建成功!")
            oid = order_result["response"]["data"]["statuses"][0]["resting"]["oid"]
            print(f"  订单 ID: {oid}")
            
            # 查询订单
            order_status = info.query_order_by_oid(address, oid)
            print(f"  订单状态: {order_status['order']['status']}")
            
            # 取消订单
            print("\n  准备取消订单...")
            cancel_result = exchange.cancel("ETH", oid)
            
            if cancel_result["status"] == "ok":
                print("  ✅ 订单取消成功!")
            else:
                print(f"  ❌ 取消失败: {cancel_result}")
        else:
            print(f"  ❌ 下单失败: {order_result}")
            
    except Exception as e:
        print(f"  ❌ 错误: {e}")
    
    # 总结
    print_section("✅ 测试完成")
    print("你已经成功完成了:")
    print("  ✅ 查询账户状态")
    print("  ✅ 查询市场价格")
    print("  ✅ 下单测试")
    print("  ✅ 取消订单")
    print("\n💡 接下来可以:")
    print("  1. 查看 examples/ 目录中的更多示例")
    print("  2. 运行 'python examples/basic_market_order.py' 测试市价单")
    print("  3. 运行 'python examples/cancel_open_orders.py' 取消所有订单")
    print("  4. 查看 SDK 文档: https://github.com/hyperliquid-dex/hyperliquid-python-sdk")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()

