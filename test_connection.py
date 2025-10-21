#!/usr/bin/env python3
"""
测试 Hyperliquid 测试网连接
此脚本不需要私钥，只查询公开信息
"""

from hyperliquid.info import Info
from hyperliquid.utils import constants

def main():
    print("=" * 60)
    print("测试 Hyperliquid 测试网连接")
    print("=" * 60)
    
    # 创建 Info 对象（不需要私钥）
    print("\n正在连接测试网...")
    info = Info(constants.TESTNET_API_URL, skip_ws=True)
    
    # 1. 获取所有币种的价格
    print("\n1. 获取市场价格:")
    all_mids = info.all_mids()
    for coin, price in list(all_mids.items())[:5]:  # 只显示前5个
        print(f"   {coin}: ${price}")
    
    # 2. 查询你的钱包地址状态
    your_address = "0xef6b0240e25b7880ab26f54c8c63034e4ac4f844"
    print(f"\n2. 查询钱包状态: {your_address}")
    
    try:
        user_state = info.user_state(your_address)
        account_value = user_state["marginSummary"]["accountValue"]
        print(f"   账户价值: ${account_value}")
        
        # 显示持仓
        positions = user_state["assetPositions"]
        if len(positions) > 0:
            print(f"   持仓数量: {len(positions)}")
            for pos in positions[:3]:  # 显示前3个持仓
                position = pos["position"]
                print(f"   - {position['coin']}: {position['szi']}")
        else:
            print("   ⚠️  当前无持仓 - 需要先获取测试币")
        
        # 查询 Spot 账户
        spot_state = info.spot_user_state(your_address)
        balances = spot_state.get("balances", [])
        if len(balances) > 0:
            print(f"\n   现货余额:")
            for balance in balances[:5]:
                print(f"   - {balance['coin']}: {balance['hold']}")
        else:
            print("\n   ⚠️  现货账户无余额 - 需要先获取测试币")
            
    except Exception as e:
        print(f"   ❌ 查询失败: {e}")
    
    print("\n" + "=" * 60)
    print("✅ 连接测试成功!")
    print("=" * 60)

if __name__ == "__main__":
    main()

