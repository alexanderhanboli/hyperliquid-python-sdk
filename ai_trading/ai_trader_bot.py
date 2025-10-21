#!/usr/bin/env python3
"""
AI 交易机器人主程序
定期拉取市场数据，调用 AI 模型，执行交易决策
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'examples'))

import json
import time
import schedule
from datetime import datetime
from typing import Dict, Any, List
import anthropic
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
        anthropic_api_key: str,
        use_testnet: bool = True,
        interval_minutes: int = 3,
        initial_capital: float = 10000.0
    ):
        """
        Args:
            coins: 交易的币种列表，如 ["BTC", "ETH", "SOL"]
            anthropic_api_key: Anthropic API key (用于调用 Claude)
            use_testnet: 是否使用测试网
            interval_minutes: 交易间隔（分钟）
            initial_capital: 初始资金
        """
        self.coins = coins
        self.interval_minutes = interval_minutes
        self.initial_capital = initial_capital
        self.use_testnet = use_testnet
        
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
        
        # 初始化 Anthropic 客户端
        self.anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)
        
        # 交易统计
        self.start_time = datetime.now()
        self.trade_count = 0
        self.returns_history = []
        
        print(f"\n{'='*80}")
        print(f"🤖 AI 交易机器人已初始化")
        print(f"{'='*80}")
        print(f"  网络: {'测试网 (Testnet)' if use_testnet else '主网 (Mainnet)'}")
        print(f"  钱包地址: {self.address}")
        print(f"  交易币种: {', '.join(coins)}")
        print(f"  交易间隔: {interval_minutes} 分钟")
        print(f"  初始资金: ${initial_capital:.2f}")
        print(f"{'='*80}\n")
    
    def run_trading_cycle(self):
        """执行一次完整的交易循环"""
        try:
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
            
            print(f"  总价值: ${total_value:.2f}")
            print(f"  可用资金: ${available_cash:.2f}")
            print(f"  总收益率: {total_return_pct:+.2f}%")
            print(f"  持仓数量: {len(current_positions)}")
            
            # 3. 构建 AI Prompt
            print("\n🧠 构建 AI Prompt...")
            prompt = self.prompt_builder.build_prompt(
                market_state=market_state,
                account_info=account_info,
                positions=current_positions
            )
            
            # 保存 prompt 到文件（用于调试）
            with open("ai_trading/last_prompt.txt", "w") as f:
                f.write(prompt)
            print(f"  Prompt 已保存到 ai_trading/last_prompt.txt")
            
            # 4. 调用 AI 模型
            print("\n🤖 调用 AI 模型 (Claude Sonnet 4.5)...")
            ai_decisions = self._call_ai_model(prompt)
            
            if not ai_decisions:
                print("❌ AI 未返回有效决策")
                return
            
            # 保存 AI 决策到文件
            with open("ai_trading/last_decision.json", "w") as f:
                json.dump(ai_decisions, f, indent=2)
            print(f"  决策已保存到 ai_trading/last_decision.json")
            
            # 5. 执行交易决策
            print("\n⚡ 执行交易决策...")
            self._execute_decisions(ai_decisions)
            
            # 6. 显示最终状态
            print("\n📈 交易循环完成")
            print(f"  账户价值: ${total_value:.2f}")
            print(f"  收益率: {total_return_pct:+.2f}%")
            print(f"{'='*80}\n")
            
        except Exception as e:
            print(f"\n❌ 交易循环出错: {e}")
            import traceback
            traceback.print_exc()
    
    def _call_ai_model(self, prompt: str) -> Dict[str, Any]:
        """调用 AI 模型获取决策"""
        try:
            # 调用 Claude API
            message = self.anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",  # Claude Sonnet 4.5
                max_tokens=4096,
                temperature=0.7,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # 提取响应内容
            response_text = message.content[0].text
            
            # 尝试从响应中提取 JSON
            # AI 可能返回的是包含 ```json ... ``` 的格式
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                decisions = json.loads(json_text)
                return decisions
            else:
                print(f"⚠️ AI 响应格式不正确:")
                print(response_text[:500])
                return {}
        
        except Exception as e:
            print(f"❌ 调用 AI 模型失败: {e}")
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
    parser.add_argument("--coins", nargs="+", default=["BTC", "ETH", "SOL"], help="交易的币种列表")
    parser.add_argument("--interval", type=int, default=3, help="交易间隔（分钟）")
    parser.add_argument("--testnet", action="store_true", default=True, help="使用测试网")
    parser.add_argument("--test", action="store_true", help="测试模式（只运行一次）")
    parser.add_argument("--api-key", type=str, help="Anthropic API Key")
    
    args = parser.parse_args()
    
    # 获取 API Key
    api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY")
    
    if not api_key:
        print("❌ 错误: 请设置 ANTHROPIC_API_KEY 环境变量或使用 --api-key 参数")
        print("\n使用方法:")
        print("  export ANTHROPIC_API_KEY='your-api-key'")
        print("  python ai_trader_bot.py")
        print("\n或:")
        print("  python ai_trader_bot.py --api-key 'your-api-key'")
        sys.exit(1)
    
    # 创建机器人
    bot = AITradingBot(
        coins=args.coins,
        anthropic_api_key=api_key,
        use_testnet=args.testnet,
        interval_minutes=args.interval
    )
    
    # 启动
    bot.start(test_mode=args.test)


if __name__ == "__main__":
    main()

