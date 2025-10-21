#!/usr/bin/env python3
"""
测试 DeepSeek API 集成
"""
import os
import sys
from openai import OpenAI

# 设置 API Key
API_KEY = 'sk-b14ed35ef1564874952a45ff819f2f7a'

print("="*80)
print("  🧪 DeepSeek API 集成测试")
print("="*80)
print()

# 测试 1: API 连接
print("1️⃣  测试 API 连接...")
try:
    client = OpenAI(
        api_key=API_KEY,
        base_url="https://api.deepseek.com"
    )
    print("   ✅ 客户端初始化成功")
except Exception as e:
    print(f"   ❌ 失败: {e}")
    sys.exit(1)

# 测试 2: deepseek-chat 模型
print("\n2️⃣  测试 deepseek-chat 模型...")
try:
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello in JSON format with a 'message' field."}
        ],
        max_tokens=100,
        temperature=0.7,
        stream=False
    )
    
    result = response.choices[0].message.content
    print(f"   ✅ deepseek-chat 响应成功")
    print(f"   响应: {result[:100]}")
    
    # 显示 token 使用情况
    if hasattr(response, 'usage'):
        print(f"   输入 tokens: {response.usage.prompt_tokens}")
        print(f"   输出 tokens: {response.usage.completion_tokens}")
        print(f"   总 tokens: {response.usage.total_tokens}")
        
        # 计算成本
        input_cost = response.usage.prompt_tokens / 1_000_000 * 0.28
        output_cost = response.usage.completion_tokens / 1_000_000 * 0.42
        total_cost = input_cost + output_cost
        print(f"   预估成本: ${total_cost:.6f}")
        
except Exception as e:
    print(f"   ❌ 失败: {e}")
    import traceback
    traceback.print_exc()

# 测试 3: deepseek-reasoner 模型
print("\n3️⃣  测试 deepseek-reasoner 模型...")
try:
    response = client.chat.completions.create(
        model="deepseek-reasoner",
        messages=[
            {"role": "system", "content": "You are an expert trading assistant."},
            {"role": "user", "content": "Should I buy BTC at $100,000? Respond in JSON with 'action' and 'reason' fields."}
        ],
        max_tokens=500,
        temperature=0.7,
        stream=False
    )
    
    result = response.choices[0].message.content
    print(f"   ✅ deepseek-reasoner 响应成功")
    print(f"   响应: {result[:200]}...")
    
    # 显示 token 使用情况
    if hasattr(response, 'usage'):
        print(f"   输入 tokens: {response.usage.prompt_tokens}")
        print(f"   输出 tokens: {response.usage.completion_tokens}")
        print(f"   总 tokens: {response.usage.total_tokens}")
        
        # 计算成本
        input_cost = response.usage.prompt_tokens / 1_000_000 * 0.28
        output_cost = response.usage.completion_tokens / 1_000_000 * 0.42
        total_cost = input_cost + output_cost
        print(f"   预估成本: ${total_cost:.6f}")
        
except Exception as e:
    print(f"   ❌ 失败: {e}")
    import traceback
    traceback.print_exc()

# 测试 4: 交易决策格式
print("\n4️⃣  测试交易决策 JSON 格式...")
try:
    prompt = """
请分析以下市场数据并给出交易决策：

BTC 价格: $100,000
RSI(14): 65.5
MACD: 150.2

请返回 JSON 格式的决策：
{
  "BTC": {
    "trade_signal_args": {
      "signal": "buy",
      "justification": "理由...",
      "coin": "BTC"
    }
  }
}
"""
    
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a trading AI. Always respond with valid JSON."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=300,
        temperature=0.7,
        stream=False
    )
    
    result = response.choices[0].message.content
    print(f"   ✅ 决策格式测试成功")
    print(f"   响应: {result[:300]}")
    
    # 尝试解析 JSON
    import json
    json_start = result.find('{')
    json_end = result.rfind('}') + 1
    if json_start != -1 and json_end > json_start:
        json_text = result[json_start:json_end]
        decision = json.loads(json_text)
        print(f"   ✅ JSON 解析成功")
        print(f"   决策内容: {json.dumps(decision, indent=2, ensure_ascii=False)[:200]}...")
    
except Exception as e:
    print(f"   ❌ 失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("  ✅ DeepSeek API 集成测试完成！")
print("="*80)
print("\n下一步:")
print("  运行完整测试: python ai_trading/test_system.py")
print("  启动交易机器人: ./ai_trading/start_deepseek.sh --test")
print("="*80 + "\n")

