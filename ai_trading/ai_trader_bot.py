#!/usr/bin/env python3
"""
AI 交易机器人主程序
定期拉取市场数据，调用 AI 模型，执行交易决策
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'examples'))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()  # 自动从 .env 文件加载环境变量

import json
import time
import schedule
from datetime import datetime
from typing import Dict, Any, List
from openai import OpenAI
from pathlib import Path
import example_utils
from hyperliquid.utils import constants

from market_data import MarketDataFetcher
from prompt_builder import PromptBuilder
from order_executor import OrderExecutor


class AITradingBot:
    """AI 交易机器人"""
    
    def __init__(
        self,
        coins: List[str],
        deepseek_api_key: str,
        use_testnet: bool = True,
        interval_minutes: int = 3,
        initial_capital: float = 10000.0,  # 已废弃，自动从账户读取
        model: str = "deepseek-reasoner"
    ):
        """
        Args:
            coins: 交易的币种列表，如 ["BTC", "ETH", "SOL"]
            deepseek_api_key: DeepSeek API key
            use_testnet: 是否使用测试网
            interval_minutes: 交易间隔（分钟）
            initial_capital: (已废弃) 初始资金会自动从实际账户余额读取
            model: DeepSeek 模型名称 (deepseek-chat 或 deepseek-reasoner)
        """
        self.coins = coins
        self.interval_minutes = interval_minutes
        self.use_testnet = use_testnet
        self.model = model
        
        # 初始化 Hyperliquid API
        base_url = constants.TESTNET_API_URL if use_testnet else constants.MAINNET_API_URL
        self.address, self.info, self.exchange = example_utils.setup(
            base_url=base_url,
            skip_ws=True
        )
        
        # 初始化各个模块
        self.market_data = MarketDataFetcher(self.info)
        self.prompt_builder = PromptBuilder(coins)
        self.order_executor = OrderExecutor(self.exchange, self.info)
        
        # 初始化 DeepSeek 客户端 (使用 OpenAI SDK)
        self.ai_client = OpenAI(
            api_key=deepseek_api_key,
            base_url="https://api.deepseek.com"
        )
        
        # 获取实际账户余额作为初始资金
        print("\n📊 正在获取账户信息...")
        actual_balance = self.order_executor.get_account_value()
        self.initial_capital = actual_balance['total_value']
        
        # 交易统计
        self.start_time = datetime.now()
        self.trade_count = 0
        self.returns_history = []
        
        # 创建历史记录目录
        self.history_dir = Path("ai_trading/history")
        self.history_dir.mkdir(parents=True, exist_ok=True)
        
        # 当前交易周期的文件夹路径（每次交易循环时创建）
        self.current_cycle_dir = None
        
        print(f"\n{'='*80}")
        print(f"🤖 AI 交易机器人已初始化")
        print(f"{'='*80}")
        print(f"  网络: {'测试网 (Testnet)' if use_testnet else '主网 (Mainnet)'}")
        print(f"  钱包地址: {self.address}")
        print(f"  交易币种: {', '.join(coins)}")
        print(f"  交易间隔: {interval_minutes} 分钟")
        print(f"  初始资金: ${self.initial_capital:.2f}")
        print(f"  可用资金: ${actual_balance['available_cash']:.2f}")
        print(f"{'='*80}\n")
    
    def run_trading_cycle(self):
        """执行一次完整的交易循环"""
        try:
            # 创建当前交易周期的文件夹
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.current_cycle_dir = self.history_dir / timestamp
            self.current_cycle_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"\n{'='*80}")
            print(f"🔄 交易循环 #{self.prompt_builder.invocation_count + 1}")
            print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*80}\n")
            
            # 1. 获取市场数据
            print("📊 获取市场数据...")
            market_state = self.market_data.get_market_state(self.coins)
            
            if not market_state:
                print("❌ 无法获取市场数据，跳过本次循环")
                return
            
            # 显示价格
            for coin, data in market_state.items():
                price = data.get('current_price', 0)
                rsi = data.get('current_rsi_14', 50)
                print(f"  {coin}: ${price:.2f} | RSI(14): {rsi:.1f}")
            
            # 2. 获取账户信息
            print("\n💰 获取账户信息...")
            account_value_info = self.order_executor.get_account_value()
            current_positions = self.order_executor.get_current_positions()
            
            total_value = account_value_info['total_value']
            available_cash = account_value_info['available_cash']
            
            # 计算收益率
            total_return_pct = ((total_value - self.initial_capital) / self.initial_capital * 100) if self.initial_capital > 0 else 0
            self.returns_history.append(total_return_pct)
            
            # 计算 Sharpe Ratio (简化版)
            sharpe_ratio = 0.0
            if len(self.returns_history) > 1:
                returns_std = max(0.01, sum([(r - sum(self.returns_history)/len(self.returns_history))**2 for r in self.returns_history]) / len(self.returns_history))**0.5
                sharpe_ratio = (total_return_pct / returns_std) if returns_std > 0 else 0
            
            account_info = {
                "total_value": total_value,
                "available_cash": available_cash,
                "total_return_pct": total_return_pct,
                "sharpe_ratio": sharpe_ratio
            }
            
            # 显示账户信息
            print(f"  总价值: ${total_value:.2f}")
            print(f"  可用资金: ${available_cash:.2f}", end="")
            
            # 保证金使用率
            total_margin = account_value_info.get('total_margin', 0)
            margin_usage = (total_margin / total_value * 100) if total_value > 0 else 0
            print(f"  已用保证金: ${total_margin:.2f} (使用率: {margin_usage:.1f}%)", end="")
            if margin_usage > 80:
                print(" ⚠️ [过高]")
            elif margin_usage > 60:
                print(" ⚠️ [偏高]")
            else:
                print()
            
            print(f"  总收益率: {total_return_pct:+.2f}%")
            print(f"  持仓数量: {len(current_positions)}")
            
            # 3. 构建 AI Prompt
            print("\n🧠 构建 AI Prompt...")
            prompt = self.prompt_builder.build_prompt(
                market_state=market_state,
                account_info=account_info,
                positions=current_positions
            )
            
            # 保存 prompt 到当前交易周期文件夹
            self._save_prompt(prompt, account_info, current_positions)
            print(f"  Prompt 已保存到 {self.current_cycle_dir.name}/")
            
            # 4. 调用 AI 模型
            print(f"\n🤖 调用 AI 模型 (DeepSeek {self.model})...")
            ai_decisions = self._call_ai_model(prompt)
            
            if not ai_decisions:
                print("❌ AI 未返回有效决策")
                return
            
            # 保存 AI 决策到当前交易周期文件夹
            self._save_decision(ai_decisions)
            print(f"  决策已保存到 {self.current_cycle_dir.name}/")
            
            # 5. 执行交易决策
            print("\n⚡ 执行交易决策...")
            self._execute_decisions(ai_decisions)
            
            # 6. 清理旧的历史记录（保持最多50个）
            self._cleanup_old_history(max_folders=50)
            
            # 7. 显示最终状态
            print("\n📈 交易循环完成")
            print(f"  账户价值: ${total_value:.2f}")
            print(f"  收益率: {total_return_pct:+.2f}%")
            print(f"{'='*80}\n")
            
        except Exception as e:
            print(f"\n❌ 交易循环出错: {e}")
            import traceback
            traceback.print_exc()
    
    def _save_prompt(self, prompt: str, account_info: Dict[str, Any], positions: List[Dict]):
        """
        保存 prompt 到当前交易周期文件夹
        同时保存摘要信息
        """
        # 保存 prompt.txt
        prompt_file = self.current_cycle_dir / "prompt.txt"
        with open(prompt_file, "w", encoding="utf-8") as f:
            f.write(prompt)
        
        # 同时保存到 last_prompt.txt (为了快速访问)
        with open("ai_trading/last_prompt.txt", "w", encoding="utf-8") as f:
            f.write(prompt)
        
        # 保存 summary.json
        summary = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "invocation_count": self.prompt_builder.invocation_count,
            "account_value": account_info.get("total_value", 0),
            "available_cash": account_info.get("available_cash", 0),
            "return_pct": account_info.get("total_return_pct", 0),
            "sharpe_ratio": account_info.get("sharpe_ratio", 0),
            "positions_count": len(positions)
        }
        
        summary_file = self.current_cycle_dir / "summary.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
    
    def _save_decision(self, decisions: Dict[str, Any]):
        """保存 AI 决策到当前交易周期文件夹"""
        # 保存到当前周期文件夹
        decision_file = self.current_cycle_dir / "decision.json"
        with open(decision_file, "w", encoding="utf-8") as f:
            json.dump(decisions, f, indent=2, ensure_ascii=False)
        
        # 同时保存到 last_decision.json (为了快速访问)
        with open("ai_trading/last_decision.json", "w", encoding="utf-8") as f:
            json.dump(decisions, f, indent=2, ensure_ascii=False)
    
    def _save_ai_response(self, response):
        """
        保存 DeepSeek API 的完整响应
        
        Args:
            response: OpenAI API 响应对象
        """
        try:
            message = response.choices[0].message
            
            # 1. 保存完整的响应内容 (response.txt)
            response_text = message.content if message.content else ""
            response_file = self.current_cycle_dir / "response.txt"
            with open(response_file, "w", encoding="utf-8") as f:
                f.write(response_text)
            
            # 2. 保存推理过程 (reasoning.txt) - 仅 deepseek-reasoner 模型有
            reasoning_content = getattr(message, 'reasoning_content', None)
            if reasoning_content:
                reasoning_file = self.current_cycle_dir / "reasoning.txt"
                with open(reasoning_file, "w", encoding="utf-8") as f:
                    f.write(reasoning_content)
            
            # 3. 保存 API 响应的元数据 (ai_response.json)
            response_metadata = {
                "model": response.model,
                "created": response.created,
                "finish_reason": response.choices[0].finish_reason,
                "has_reasoning": reasoning_content is not None,
                "reasoning_length": len(reasoning_content) if reasoning_content else 0,
                "response_length": len(response_text),
            }
            
            # 添加 token 使用信息（如果有的话）
            if hasattr(response, 'usage') and response.usage:
                usage_data = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
                # 添加 DeepSeek Context Caching 信息
                if hasattr(response.usage, 'prompt_cache_hit_tokens'):
                    usage_data["prompt_cache_hit_tokens"] = response.usage.prompt_cache_hit_tokens
                if hasattr(response.usage, 'prompt_cache_miss_tokens'):
                    usage_data["prompt_cache_miss_tokens"] = response.usage.prompt_cache_miss_tokens
                
                response_metadata["usage"] = usage_data
            
            response_metadata_file = self.current_cycle_dir / "ai_response.json"
            with open(response_metadata_file, "w", encoding="utf-8") as f:
                json.dump(response_metadata, f, indent=2, ensure_ascii=False)
            
            # 显示保存信息，包括 cache hit 统计
            usage_info = response_metadata.get('usage', {})
            total_tokens = usage_info.get('total_tokens', 'N/A')
            cache_hit = usage_info.get('prompt_cache_hit_tokens', 0)
            cache_miss = usage_info.get('prompt_cache_miss_tokens', 0)
            
            print(f"  ✅ AI 响应已保存 (reasoning: {response_metadata['has_reasoning']}, " +
                  f"tokens: {total_tokens})")
            
            # 如果有 cache 信息，显示 cache hit 率
            if cache_hit > 0 or cache_miss > 0:
                total_prompt = cache_hit + cache_miss
                cache_rate = (cache_hit / total_prompt * 100) if total_prompt > 0 else 0
                print(f"  📊 Cache Hit: {cache_hit} tokens ({cache_rate:.1f}%), " +
                      f"Cache Miss: {cache_miss} tokens")
        
        except Exception as e:
            print(f"  ⚠️ 保存 AI 响应失败: {e}")
    
    def _cleanup_old_history(self, max_folders: int = 50):
        """删除超过 max_folders 数量的旧交易周期文件夹"""
        history_folders = sorted(
            [d for d in self.history_dir.iterdir() if d.is_dir()],
            key=lambda p: p.stat().st_mtime,
            reverse=True  # 最新的在前面
        )
        
        # 如果文件夹数量超过 max_folders，删除旧的
        if len(history_folders) > max_folders:
            for old_folder in history_folders[max_folders:]:
                try:
                    # 删除文件夹内的所有文件
                    for file in old_folder.iterdir():
                        file.unlink()
                    # 删除文件夹
                    old_folder.rmdir()
                except Exception as e:
                    print(f"  ⚠️ 无法删除旧文件夹 {old_folder}: {e}")
    
    def _call_ai_model(self, prompt: str) -> Dict[str, Any]:
        """调用 AI 模型获取决策"""
        try:
            # 根据模型设置最大输出 tokens
            # deepseek-chat: 最大 8K, deepseek-reasoner: 最大 64K
            max_tokens = 64000 if self.model == "deepseek-reasoner" else 8000
            
            # 获取系统 prompt（固定内容，可被 DeepSeek Context Caching 缓存）
            system_prompt = self.prompt_builder.build_system_prompt()
            
            # 调用 DeepSeek API (使用 OpenAI SDK)
            # system prompt 包含所有固定的指令和规则，能够被缓存
            # user prompt 只包含实时变化的市场数据和账户信息
            # 使用 JSON mode 保证返回格式正确
            response = self.ai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={
                    "type": "json_object"
                },
                temperature=0.7,
                max_tokens=max_tokens,
                stream=False
            )
            
            # 保存完整的 AI 响应
            self._save_ai_response(response)

            # 提取响应内容
            response_text = response.choices[0].message.content

            # 由于使用了 JSON mode，响应保证是有效的 JSON
            try:
                decisions = json.loads(response_text)

                # 验证格式：确保是 { "COIN": { "trade_signal_args": {...} } } 格式
                if not isinstance(decisions, dict):
                    print(f"⚠️ AI 返回的不是 JSON 对象")
                    return {}

                # 检查至少有一个有效的决策
                has_valid_decision = False
                for coin, data in decisions.items():
                    if isinstance(data, dict) and "trade_signal_args" in data:
                        has_valid_decision = True
                    else:
                        print(f"⚠️ {coin} 的决策格式不正确，缺少 trade_signal_args")

                if not has_valid_decision:
                    print(f"⚠️ 没有找到有效的交易决策")
                    print(f"返回的数据: {json.dumps(decisions, indent=2)[:300]}")
                    return {}

                return decisions

            except json.JSONDecodeError as e:
                print(f"❌ JSON 解析失败: {e}")
                print(f"响应内容: {response_text[:500]}")
                return {}
        
        except Exception as e:
            print(f"❌ 调用 AI 模型失败: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def _execute_decisions(self, decisions: Dict[str, Any]):
        """执行 AI 的交易决策"""
        if not decisions:
            print("  没有决策需要执行")
            return
        
        for coin, decision_wrapper in decisions.items():
            if "trade_signal_args" not in decision_wrapper:
                continue
            
            decision = decision_wrapper["trade_signal_args"]
            signal = decision.get("signal", "").lower()
            
            print(f"\n  [{coin}] 信号: {signal.upper()}")
            
            if "justification" in decision:
                print(f"    理由: {decision['justification']}")
            
            # 执行决策
            result = self.order_executor.execute_decision(decision)
            
            if result.get("status") == "ok":
                self.trade_count += 1
                print(f"    ✅ 执行成功")
            elif result.get("status") == "skipped":
                print(f"    ⏭️ {result.get('message')}")
            else:
                print(f"    ❌ 执行失败: {result.get('message')}")
    
    def start(self, test_mode: bool = False):
        """启动交易机器人"""
        print(f"\n{'='*80}")
        print(f"🚀 启动 AI 交易机器人")
        print(f"{'='*80}")
        
        if test_mode:
            print("\n⚠️ 测试模式：只运行一次")
            self.run_trading_cycle()
            return
        
        print(f"  交易间隔: 每 {self.interval_minutes} 分钟")
        print(f"  按 Ctrl+C 停止机器人")
        print(f"{'='*80}\n")
        
        # 立即执行一次
        self.run_trading_cycle()
        
        # 设置定时任务
        schedule.every(self.interval_minutes).minutes.do(self.run_trading_cycle)
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n👋 机器人已停止")
            self._print_summary()
    
    def _print_summary(self):
        """打印交易总结"""
        elapsed_time = datetime.now() - self.start_time
        account_value = self.order_executor.get_account_value()
        total_value = account_value['total_value']
        final_return = ((total_value - self.initial_capital) / self.initial_capital * 100) if self.initial_capital > 0 else 0
        
        print(f"\n{'='*80}")
        print(f"📊 交易总结")
        print(f"{'='*80}")
        print(f"  运行时长: {elapsed_time}")
        print(f"  交易次数: {self.trade_count}")
        print(f"  初始资金: ${self.initial_capital:.2f}")
        print(f"  最终价值: ${total_value:.2f}")
        print(f"  总收益: ${total_value - self.initial_capital:+.2f}")
        print(f"  收益率: {final_return:+.2f}%")
        print(f"{'='*80}\n")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI 交易机器人")
    parser.add_argument("--coins", nargs="+", help="交易的币种列表")
    parser.add_argument("--top-coins", type=int, help="按市值排序交易前N个币种")
    parser.add_argument("--interval", type=int, default=3, help="交易间隔（分钟）")
    parser.add_argument("--testnet", action="store_true", default=True, help="使用测试网")
    parser.add_argument("--test", action="store_true", help="测试模式（只运行一次）")
    parser.add_argument("--api-key", type=str, help="DeepSeek API Key")
    parser.add_argument("--model", type=str, default="deepseek-reasoner", choices=["deepseek-chat", "deepseek-reasoner"], help="DeepSeek 模型")
    
    args = parser.parse_args()
    
    # 获取 API Key
    api_key = args.api_key or os.environ.get("DEEPSEEK_API_KEY")
    
    if not api_key:
        print("❌ 错误: 请设置 DEEPSEEK_API_KEY 环境变量或使用 --api-key 参数")
        print("\n使用方法:")
        print("  export DEEPSEEK_API_KEY='your-api-key'")
        print("  python ai_trader_bot.py")
        print("\n或:")
        print("  python ai_trader_bot.py --api-key 'your-api-key'")
        sys.exit(1)

    # 参数验证
    if args.coins and args.top_coins:
        print("❌ 错误: --coins 和 --top-coins 参数不能同时指定")
        print("\n使用方法:")
        print("  指定具体币种: python ai_trader_bot.py --coins BTC ETH SOL")
        print("  按市值排序: python ai_trader_bot.py --top-coins 20")
        sys.exit(1)

    if not args.coins and not args.top_coins:
        print("❌ 错误: 必须指定 --coins 或 --top-coins 参数")
        print("\n使用方法:")
        print("  指定具体币种: python ai_trader_bot.py --coins BTC ETH SOL")
        print("  按市值排序: python ai_trader_bot.py --top-coins 20")
        sys.exit(1)

    # 确定交易币种
    if args.top_coins:
        print(f"📊 正在获取市值前 {args.top_coins} 名的币种...")

        # 创建临时 MarketDataFetcher 来获取市值排序的币种
        base_url = constants.TESTNET_API_URL if args.testnet else constants.MAINNET_API_URL
        address, info, exchange = example_utils.setup(
            base_url=base_url,
            skip_ws=True
        )

        market_data = MarketDataFetcher(info)
        coins = market_data.get_top_coins_by_market_cap(args.top_coins)

        print(f"✅ 选择的币种: {', '.join(coins)}")
    else:
        coins = args.coins

    # 创建机器人
    bot = AITradingBot(
        coins=coins,
        deepseek_api_key=api_key,
        use_testnet=args.testnet,
        interval_minutes=args.interval,
        model=args.model
    )
    
    # 启动
    bot.start(test_mode=args.test)


if __name__ == "__main__":
    main()

