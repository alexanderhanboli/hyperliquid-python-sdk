#!/usr/bin/env python3
"""
验证 Hyperliquid SDK 配置是否正确
包括私钥、地址匹配和测试网余额检查
"""

import sys
import os
import json

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

import eth_account
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants

def main():
    print("=" * 70)
    print("🔍 验证 Hyperliquid SDK 配置")
    print("=" * 70)
    
    # 1. 检查配置文件
    config_path = os.path.join(os.path.dirname(__file__), "examples", "config.json")
    
    print("\n1️⃣  检查配置文件...")
    if not os.path.exists(config_path):
        print("   ❌ 配置文件不存在: examples/config.json")
        return False
    
    with open(config_path) as f:
        config = json.load(f)
    
    secret_key = config.get("secret_key", "")
    account_address = config.get("account_address", "")
    
    # 2. 验证私钥格式
    print("\n2️⃣  验证私钥格式...")
    if not secret_key or secret_key == "YOUR_PRIVATE_KEY_HERE":
        print("   ❌ 私钥未配置！")
        print("   请编辑 examples/config.json 文件")
        print("   将 'secret_key' 设置为你的钱包私钥")
        return False
    
    if not secret_key.startswith("0x"):
        print("   ❌ 私钥格式错误：必须以 0x 开头")
        return False
    
    if len(secret_key) != 66:
        print(f"   ❌ 私钥长度错误：应该是 66 个字符，当前是 {len(secret_key)} 个")
        return False
    
    print("   ✅ 私钥格式正确")
    
    # 3. 验证私钥和地址是否匹配
    print("\n3️⃣  验证私钥和地址匹配...")
    try:
        account = eth_account.Account.from_key(secret_key)
        derived_address = account.address.lower()
        
        if account_address:
            expected_address = account_address.lower()
            if derived_address != expected_address:
                print(f"   ❌ 地址不匹配！")
                print(f"      配置的地址: {account_address}")
                print(f"      私钥对应地址: {account.address}")
                return False
        
        print(f"   ✅ 地址匹配: {account.address}")
        
    except Exception as e:
        print(f"   ❌ 私钥无效: {e}")
        return False
    
    # 4. 测试连接测试网
    print("\n4️⃣  连接测试网...")
    try:
        info = Info(constants.TESTNET_API_URL, skip_ws=True)
        print("   ✅ 测试网连接成功")
    except Exception as e:
        print(f"   ❌ 连接失败: {e}")
        return False
    
    # 5. 查询余额
    print("\n5️⃣  查询账户余额...")
    try:
        user_state = info.user_state(account.address)
        account_value = user_state["marginSummary"]["accountValue"]
        print(f"   💰 账户价值: ${account_value}")
        
        if float(account_value) == 0:
            spot_state = info.spot_user_state(account.address)
            balances = spot_state.get("balances", [])
            
            if len(balances) == 0:
                print("   ⚠️  警告: 账户余额为 0")
                print("   请确认已在测试网领取测试币")
            else:
                print("\n   现货余额:")
                for balance in balances[:5]:
                    print(f"   - {balance['coin']}: {balance['hold']}")
        else:
            positions = user_state["assetPositions"]
            if len(positions) > 0:
                print(f"\n   持仓数量: {len(positions)}")
                for pos in positions[:3]:
                    position = pos["position"]
                    print(f"   - {position['coin']}: {position['szi']}")
        
    except Exception as e:
        print(f"   ❌ 查询失败: {e}")
        return False
    
    # 6. 测试 Exchange 对象创建
    print("\n6️⃣  测试 Exchange 对象...")
    try:
        exchange = Exchange(
            account, 
            base_url=constants.TESTNET_API_URL,
            account_address=account.address
        )
        print("   ✅ Exchange 对象创建成功")
    except Exception as e:
        print(f"   ❌ 创建失败: {e}")
        return False
    
    # 总结
    print("\n" + "=" * 70)
    print("✅ 所有检查通过！配置完全正确！")
    print("=" * 70)
    print("\n🚀 你现在可以运行示例代码了:")
    print("   cd examples")
    print("   python basic_order.py")
    print("\n📚 查看所有示例:")
    print("   ls examples/basic_*.py")
    print("=" * 70)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

