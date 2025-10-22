#!/usr/bin/env python3
"""
测试 RSI 背离检测功能
"""

from market_data import TechnicalIndicators

def test_bearish_divergence():
    """测试顶背离检测"""
    print("=" * 80)
    print("测试 1: 顶背离 (Bearish Divergence)")
    print("=" * 80)
    
    # 价格创新高，但 RSI 未创新高
    prices = [100, 102, 101, 103, 102, 104, 103, 106, 105, 108, 107, 110, 109, 111, 110]
    rsi_values = [50, 55, 52, 58, 54, 60, 56, 62, 58, 60, 56, 58, 54, 56, 52]
    
    result = TechnicalIndicators.detect_rsi_divergence(prices, rsi_values)
    
    print(f"\n价格序列: {prices}")
    print(f"RSI 序列:  {rsi_values}")
    print(f"\n检测结果:")
    print(f"  有背离: {result['has_divergence']}")
    print(f"  类型: {result['divergence_type']}")
    print(f"  强度: {result['divergence_strength']}")
    print(f"  描述: {result['description']}")
    print()

def test_bullish_divergence():
    """测试底背离检测"""
    print("=" * 80)
    print("测试 2: 底背离 (Bullish Divergence)")
    print("=" * 80)
    
    # 价格创新低，但 RSI 未创新低
    prices = [110, 108, 109, 106, 107, 104, 105, 102, 103, 100, 101, 98, 99, 96, 97]
    rsi_values = [50, 45, 48, 42, 44, 38, 40, 36, 38, 34, 36, 38, 40, 42, 44]
    
    result = TechnicalIndicators.detect_rsi_divergence(prices, rsi_values)
    
    print(f"\n价格序列: {prices}")
    print(f"RSI 序列:  {rsi_values}")
    print(f"\n检测结果:")
    print(f"  有背离: {result['has_divergence']}")
    print(f"  类型: {result['divergence_type']}")
    print(f"  强度: {result['divergence_strength']}")
    print(f"  描述: {result['description']}")
    print()

def test_no_divergence():
    """测试无背离情况"""
    print("=" * 80)
    print("测试 3: 无背离 (价格和 RSI 同向)")
    print("=" * 80)
    
    # 价格和 RSI 都上涨
    prices = [100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120, 122, 124, 126, 128]
    rsi_values = [45, 48, 51, 54, 57, 60, 63, 66, 69, 72, 75, 78, 81, 84, 87]
    
    result = TechnicalIndicators.detect_rsi_divergence(prices, rsi_values)
    
    print(f"\n价格序列: {prices}")
    print(f"RSI 序列:  {rsi_values}")
    print(f"\n检测结果:")
    print(f"  有背离: {result['has_divergence']}")
    print(f"  类型: {result['divergence_type']}")
    print(f"  描述: {result['description']}")
    print()

def test_strength_levels():
    """测试不同强度的背离"""
    print("=" * 80)
    print("测试 4: 不同强度的背离")
    print("=" * 80)
    
    # 强背离 (RSI 差异 > 10)
    print("\n4.1 强背离 (Strong):")
    prices1 = [100, 102, 101, 103, 102, 104, 103, 106, 105, 108, 107, 110, 109, 112, 111]
    rsi1 = [50, 60, 58, 62, 60, 65, 63, 68, 66, 70, 68, 65, 62, 55, 52]  # 差异 > 10
    result1 = TechnicalIndicators.detect_rsi_divergence(prices1, rsi1)
    print(f"  强度: {result1['divergence_strength']}")
    print(f"  描述: {result1['description']}")
    
    # 中等背离 (RSI 差异 5-10)
    print("\n4.2 中等背离 (Moderate):")
    prices2 = [100, 102, 101, 103, 102, 104, 103, 106, 105, 108, 107, 110, 109, 112, 111]
    rsi2 = [50, 58, 56, 60, 58, 62, 60, 64, 62, 66, 64, 62, 60, 58, 56]  # 差异 5-10
    result2 = TechnicalIndicators.detect_rsi_divergence(prices2, rsi2)
    print(f"  强度: {result2['divergence_strength']}")
    print(f"  描述: {result2['description']}")
    
    # 弱背离 (RSI 差异 < 5)
    print("\n4.3 弱背离 (Weak):")
    prices3 = [100, 102, 101, 103, 102, 104, 103, 106, 105, 108, 107, 110, 109, 112, 111]
    rsi3 = [50, 56, 54, 58, 56, 60, 58, 62, 60, 64, 62, 63, 62, 61, 60]  # 差异 < 5
    result3 = TechnicalIndicators.detect_rsi_divergence(prices3, rsi3)
    print(f"  强度: {result3['divergence_strength']}")
    print(f"  描述: {result3['description']}")
    print()

if __name__ == "__main__":
    print("\n🔬 RSI 背离检测功能测试\n")
    
    test_bearish_divergence()
    test_bullish_divergence()
    test_no_divergence()
    test_strength_levels()
    
    print("=" * 80)
    print("✅ 所有测试完成！")
    print("=" * 80)

