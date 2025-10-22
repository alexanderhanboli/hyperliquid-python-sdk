#!/usr/bin/env python3
"""
查看和分析交易历史记录的工具脚本
"""

import json
from pathlib import Path
import sys
from datetime import datetime


def list_history_sessions(limit=10):
    """列出最近的交易周期"""
    history_dir = Path("ai_trading/history")
    
    if not history_dir.exists():
        print("❌ 历史记录目录不存在")
        return []
    
    folders = sorted(
        [d for d in history_dir.iterdir() if d.is_dir()],
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )[:limit]
    
    print(f"\n📊 最近 {len(folders)} 次交易周期:\n")
    print(f"{'序号':<4} {'时间':<20} {'账户价值':<12} {'收益率':<10} {'持仓':<6} {'推理':<6}")
    print("-" * 70)
    
    for i, folder in enumerate(folders, 1):
        summary_file = folder / "summary.json"
        ai_response_file = folder / "ai_response.json"
        
        if summary_file.exists():
            with open(summary_file, 'r', encoding='utf-8') as f:
                summary = json.load(f)
        else:
            summary = {}
        
        has_reasoning = False
        if ai_response_file.exists():
            with open(ai_response_file, 'r', encoding='utf-8') as f:
                ai_resp = json.load(f)
                has_reasoning = ai_resp.get('has_reasoning', False)
        
        timestamp = summary.get('timestamp', folder.name)
        account_value = summary.get('account_value', 0)
        return_pct = summary.get('return_pct', 0)
        positions_count = summary.get('positions_count', 0)
        
        print(f"{i:<4} {timestamp:<20} ${account_value:<11.2f} {return_pct:>+7.2f}%  {positions_count:<6} {'✓' if has_reasoning else '✗':<6}")
    
    return folders


def show_session_details(session_path):
    """显示单个交易周期的详细信息"""
    session_path = Path(session_path)
    
    if not session_path.exists():
        print(f"❌ 路径不存在: {session_path}")
        return
    
    print(f"\n{'='*70}")
    print(f"📁 交易周期: {session_path.name}")
    print(f"{'='*70}")
    
    # 摘要信息
    summary_file = session_path / "summary.json"
    if summary_file.exists():
        with open(summary_file, 'r', encoding='utf-8') as f:
            summary = json.load(f)
        
        print("\n📊 摘要信息:")
        print(f"  时间: {summary.get('timestamp', 'N/A')}")
        print(f"  账户价值: ${summary.get('account_value', 0):.2f}")
        print(f"  可用资金: ${summary.get('available_cash', 0):.2f}")
        print(f"  收益率: {summary.get('return_pct', 0):+.2f}%")
        print(f"  夏普比率: {summary.get('sharpe_ratio', 0):.2f}")
        print(f"  持仓数量: {summary.get('positions_count', 0)}")
    
    # AI 响应信息
    ai_response_file = session_path / "ai_response.json"
    if ai_response_file.exists():
        with open(ai_response_file, 'r', encoding='utf-8') as f:
            ai_resp = json.load(f)
        
        print("\n🤖 AI 响应:")
        print(f"  模型: {ai_resp.get('model', 'N/A')}")
        print(f"  完成原因: {ai_resp.get('finish_reason', 'N/A')}")
        print(f"  有推理过程: {'是' if ai_resp.get('has_reasoning') else '否'}")
        
        if ai_resp.get('has_reasoning'):
            print(f"  推理长度: {ai_resp.get('reasoning_length', 0):,} 字符")
        
        print(f"  响应长度: {ai_resp.get('response_length', 0):,} 字符")
        
        if 'usage' in ai_resp:
            usage = ai_resp['usage']
            print(f"  Token 使用:")
            print(f"    - Prompt: {usage.get('prompt_tokens', 0):,}")
            print(f"    - Completion: {usage.get('completion_tokens', 0):,}")
            print(f"    - 总计: {usage.get('total_tokens', 0):,}")
    
    # 决策信息
    decision_file = session_path / "decision.json"
    if decision_file.exists():
        with open(decision_file, 'r', encoding='utf-8') as f:
            decisions = json.load(f)
        
        print("\n💡 交易决策:")
        for coin, data in decisions.items():
            args = data.get('trade_signal_args', {})
            signal = args.get('signal', 'unknown')
            
            if signal == 'entry':
                direction = "做多" if args.get('is_buy') else "做空"
                print(f"  • {coin}: 开仓 {direction}")
                print(f"      数量: {args.get('quantity', 0)}")
                print(f"      止损: ${args.get('stop_loss', 0):.2f}")
                print(f"      止盈: ${args.get('profit_target', 0):.2f}")
                print(f"      杠杆: {args.get('leverage', 0)}x")
                print(f"      理由: {args.get('justification', 'N/A')}")
            elif signal == 'hold':
                print(f"  • {coin}: 持仓")
                print(f"      数量: {args.get('quantity', 0)}")
            elif signal == 'close':
                print(f"  • {coin}: 平仓")
                print(f"      数量: {args.get('quantity', 0)}")
                print(f"      理由: {args.get('justification', 'N/A')}")
    
    # 文件列表
    print("\n📄 包含文件:")
    files = sorted(session_path.iterdir())
    for file in files:
        if file.is_file():
            size = file.stat().st_size
            size_str = f"{size:,} bytes" if size < 1024 else f"{size/1024:.1f} KB"
            print(f"  • {file.name:<20} ({size_str})")
    
    print()


def show_reasoning(session_path):
    """显示推理过程"""
    session_path = Path(session_path)
    reasoning_file = session_path / "reasoning.txt"
    
    if not reasoning_file.exists():
        print(f"❌ 该交易周期没有推理记录")
        print(f"   提示: 只有 deepseek-reasoner 模型才会生成推理记录")
        return
    
    with open(reasoning_file, 'r', encoding='utf-8') as f:
        reasoning = f.read()
    
    print(f"\n{'='*70}")
    print(f"🧠 推理过程 ({len(reasoning):,} 字符)")
    print(f"{'='*70}\n")
    print(reasoning)
    print()


def show_response(session_path):
    """显示完整响应"""
    session_path = Path(session_path)
    response_file = session_path / "response.txt"
    
    if not response_file.exists():
        print(f"❌ 响应文件不存在")
        return
    
    with open(response_file, 'r', encoding='utf-8') as f:
        response = f.read()
    
    print(f"\n{'='*70}")
    print(f"📝 AI 响应 ({len(response):,} 字符)")
    print(f"{'='*70}\n")
    print(response)
    print()


def token_statistics():
    """统计 token 使用情况"""
    history_dir = Path("ai_trading/history")
    
    if not history_dir.exists():
        print("❌ 历史记录目录不存在")
        return
    
    folders = sorted(
        [d for d in history_dir.iterdir() if d.is_dir()],
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    
    total_tokens = 0
    total_prompt_tokens = 0
    total_completion_tokens = 0
    count = 0
    
    print(f"\n📊 Token 使用统计:\n")
    print(f"{'时间':<20} {'Prompt':<10} {'Completion':<12} {'总计':<10}")
    print("-" * 55)
    
    for folder in folders:
        ai_response_file = folder / "ai_response.json"
        
        if ai_response_file.exists():
            with open(ai_response_file, 'r', encoding='utf-8') as f:
                ai_resp = json.load(f)
            
            if 'usage' in ai_resp:
                usage = ai_resp['usage']
                prompt = usage.get('prompt_tokens', 0)
                completion = usage.get('completion_tokens', 0)
                total = usage.get('total_tokens', 0)
                
                total_tokens += total
                total_prompt_tokens += prompt
                total_completion_tokens += completion
                count += 1
                
                # 从 summary.json 获取时间戳
                summary_file = folder / "summary.json"
                if summary_file.exists():
                    with open(summary_file, 'r', encoding='utf-8') as f:
                        summary = json.load(f)
                        timestamp = summary.get('timestamp', folder.name)
                else:
                    timestamp = folder.name
                
                print(f"{timestamp:<20} {prompt:<10,} {completion:<12,} {total:<10,}")
    
    if count > 0:
        print("-" * 55)
        print(f"{'平均:':<20} {total_prompt_tokens/count:<10,.0f} {total_completion_tokens/count:<12,.0f} {total_tokens/count:<10,.0f}")
        print(f"{'总计:':<20} {total_prompt_tokens:<10,} {total_completion_tokens:<12,} {total_tokens:<10,}")
        print(f"\n总共 {count} 次调用")
    else:
        print("没有找到 token 使用记录")
    
    print()


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("\n用法:")
        print("  python view_history.py list [数量]        - 列出最近的交易周期")
        print("  python view_history.py show <路径>        - 显示交易周期详情")
        print("  python view_history.py reasoning <路径>   - 显示推理过程")
        print("  python view_history.py response <路径>    - 显示完整响应")
        print("  python view_history.py tokens             - Token 使用统计")
        print("\n示例:")
        print("  python view_history.py list 5")
        print("  python view_history.py show ai_trading/history/20251022_114938")
        print("  python view_history.py reasoning ai_trading/history/20251022_114938")
        print()
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "list":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        list_history_sessions(limit)
    
    elif command == "show":
        if len(sys.argv) < 3:
            print("❌ 请指定交易周期路径")
            sys.exit(1)
        show_session_details(sys.argv[2])
    
    elif command == "reasoning":
        if len(sys.argv) < 3:
            print("❌ 请指定交易周期路径")
            sys.exit(1)
        show_reasoning(sys.argv[2])
    
    elif command == "response":
        if len(sys.argv) < 3:
            print("❌ 请指定交易周期路径")
            sys.exit(1)
        show_response(sys.argv[2])
    
    elif command == "tokens":
        token_statistics()
    
    else:
        print(f"❌ 未知命令: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
