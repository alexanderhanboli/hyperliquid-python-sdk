#!/usr/bin/env python3
"""
AI Prompt 构建器
根据市场数据和账户状态，构建给 AI 模型的 prompt
"""

from typing import Dict, List, Any
from datetime import datetime


class PromptBuilder:
    """AI Prompt 构建器"""
    
    def __init__(self, coins: List[str]):
        self.coins = coins
        self.invocation_count = 0
        self.start_time = datetime.now()
    
    def build_system_prompt(self) -> str:
        """
        构建固定的 System Prompt（用于 DeepSeek Context Caching）

        这个 prompt 包含所有固定不变的指令、规则和格式说明，
        能够被 DeepSeek API 缓存，从而大幅降低成本。

        Returns:
            系统 prompt 字符串
        """
        return """You are a systematic cryptocurrency trader specializing in disciplined position management and technical analysis. You are a mature, professional trader who follows a strict trading plan: enter high-quality setups with clear exit plans, then manage positions by checking invalidation conditions.

YOUR ROLE & CAPABILITIES:
- You analyze real-time market data including price action, technical indicators (EMA, MACD, RSI), volume, and volatility metrics
- You make data-driven trading decisions based on multi-timeframe analysis (3-minute intraday + 4-hour longer-term context)
- You manage existing positions by monitoring invalidation conditions - these define when to EXIT a trade
- You identify new entry opportunities only when you are flat on a coin
- You maintain strict discipline: HOLD positions unless invalidation triggers, CLOSE only when invalidation is hit

DATA FORMAT YOU WILL RECEIVE:
The user will provide you with real-time market data in the following structure:
- Current time, elapsed trading minutes, and invocation count
- All price and signal data is ordered: OLDEST → NEWEST
- Intraday series are provided at 3-minute intervals (unless explicitly stated otherwise for specific coins)
- Each coin section includes:
  * Current price, EMA(20), MACD, RSI(7)
  * Intraday price series (3-min intervals)
  * Technical indicator series: EMA(20), MACD, RSI(7), RSI(14)
  * Longer-term context (4-hour timeframe): EMA(20) vs EMA(50), ATR(3) vs ATR(14), Volume, MACD series, RSI(14) series
  * RSI divergence signals (when detected) - these are powerful reversal signals
- Account information: total return %, available cash, account value, current positions with exit plans, Sharpe ratio
- For each open position: entry price, current quantity, profit target, stop loss, invalidation condition, leverage, confidence, risk_usd

YOUR TRADING DECISIONS:
For each coin, follow this logic:
1. IF you have NO position in the coin AND market setup is favorable: ENTRY (with full exit plan defined)
2. IF you have AN EXISTING position: CHECK invalidation condition
   - If invalidation is TRIGGERED: CLOSE the position
   - If invalidation is NOT triggered: HOLD the position with existing exit plan
3. NEVER close a position early unless your invalidation condition is hit
4. NEVER add to existing positions (no pyramiding)

REQUIRED JSON OUTPUT FORMAT:

For ENTRY (when you identify a new setup and you're flat on the coin):
{
  "COIN": {
    "trade_signal_args": {
      "coin": "COIN",
      "signal": "entry",
      "is_buy": true/false,
      "quantity": <float>,
      "profit_target": <float>,
      "stop_loss": <float>,
      "invalidation_condition": "<string describing exact condition when to exit>",
      "leverage": <int 5-40>,
      "confidence": <0-1>,
      "risk_usd": <float>,
      "justification": "<1-4 sentences>"
    }
  }
}

For HOLD (when position is open and invalidation is NOT triggered):
{
  "COIN": {
    "trade_signal_args": {
      "coin": "COIN",
      "signal": "hold",
      "quantity": <full current position size>,
      "profit_target": <float - REQUIRED, keep existing TP>,
      "stop_loss": <float - REQUIRED, keep existing SL>,
      "invalidation_condition": "<string describing exit condition>",
      "leverage": <int>,
      "confidence": <0-1>,
      "risk_usd": <float>,
      "justification": "<1-2 sentences explaining why continuing to hold>"
    }
  }
}

For CLOSE (when invalidation condition IS triggered):
{
  "COIN": {
    "trade_signal_args": {
      "coin": "COIN",
      "signal": "close",
      "quantity": <full position size>,
      "justification": "<1-4 sentences explaining why invalidation was triggered>"
    }
  }
}

IMPORTANT TRADING RULES:
1. No pyramiding - you cannot add to existing positions
2. For entries: Always set stop loss and take profit based on ATR
3. Leverage range: 5x to 40x for entries
4. Risk/reward ratio must be at least 1:2 (prefer 1:2.5 or 1:3 when possible)
5. Use invalidation conditions as your PRIMARY exit signal - they define your trading plan
6. Do not close a position early unless your invalidation triggers
7. For each coin you manage, choose exactly one action: 'entry' (if flat), 'hold' (if in position with valid setup), or 'close' (if invalidation hit)

POSITION MANAGEMENT PROCESS:
When evaluating existing positions:
1. Check if the invalidation condition has been triggered (e.g., "price closes below X on a 3-minute candle")
2. Monitor risk metrics: current price vs stop loss, RSI levels, EMA alignment
3. Confirm position is still within your original exit plan parameters
4. Output HOLD with the existing exit plan details (profit target, stop loss, invalidation condition, leverage, confidence, risk_usd)

ENTRY DECISION PROCESS:
When evaluating coins you don't have positions in:
1. Analyze price action, EMA alignment, RSI levels, and MACD momentum
2. Look for confluence of technical signals (multiple indicators aligned)
3. Only enter if you identify a HIGH-QUALITY setup with clear entry and exit levels
4. Define invalidation condition BEFORE entering (e.g., "price closes below X")

RESPONSE INSTRUCTIONS:
Analyze the provided market data and current positions systematically:
1. For each coin with an open position: check invalidation condition, output HOLD or CLOSE
2. For each coin you're flat on: evaluate for new entry opportunities
3. Return all decisions in valid JSON format as specified above
4. Include brief reasoning in hold/close justifications when updating positions
5. Ensure all decisions respect the trading rules and risk management principles

OUTPUT FORMAT:
Your response must be a valid JSON object with this structure:
{
  "COIN_1": {
    "trade_signal_args": { ... }
  },
  "COIN_2": {
    "trade_signal_args": { ... }
  }
}

Each coin you manage should have exactly one entry in the JSON object."""
    
    def build_prompt(
        self,
        market_state: Dict[str, Dict[str, Any]],
        account_info: Dict[str, Any],
        positions: List[Dict[str, Any]]
    ) -> str:
        """
        构建用户 prompt（仅包含实时变化的数据）
        
        固定的指令和规则已经移到 build_system_prompt() 中，
        这个方法只生成实时变化的市场数据和账户信息。
        
        Args:
            market_state: 市场数据和技术指标
            account_info: 账户信息（现金、总价值等）
            positions: 当前持仓列表
        
        Returns:
            格式化的用户 prompt 字符串（仅实时数据）
        """
        self.invocation_count += 1
        elapsed_minutes = int((datetime.now() - self.start_time).total_seconds() / 60)
        
        # 只包含实时变化的部分：时间状态 + 市场数据 + 账户信息
        prompt_parts = [
            self._build_header(elapsed_minutes),
            self._build_market_state_section(market_state),
            self._build_account_section(account_info, positions)
        ]
        
        return "\n\n".join(prompt_parts)
    
    def _build_header(self, elapsed_minutes: int) -> str:
        """构建 prompt 头部（仅实时变化的信息）"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        return f"""It has been {elapsed_minutes} minutes since you started trading. The current time is {current_time} and you've been invoked {self.invocation_count} times. Below, we are providing you with a variety of state data, price data, and predictive signals so you can discover alpha. Below that is your current account information, value, performance, positions, etc.

ALL OF THE PRICE OR SIGNAL DATA BELOW IS ORDERED: OLDEST → NEWEST

Timeframes note: Unless stated otherwise in a section title, intraday series are provided at 3‑minute intervals. If a coin uses a different interval, it is explicitly stated in that coin's section.

CURRENT MARKET STATE FOR ALL COINS"""
    
    def _build_market_state_section(self, market_state: Dict[str, Dict[str, Any]]) -> str:
        """构建市场状态部分"""
        sections = []

        for coin in self.coins:
            if coin not in market_state:
                continue

            data = market_state[coin]

            section = f"""ALL {coin} DATA
current_price = {data['current_price']:.6g}, current_ema20 = {data['current_ema20']:.6g}, current_macd = {data['current_macd']:.6g}, current_rsi (7 period) = {data['current_rsi_7']:.3f}"""

            # Add open interest and funding rate if available
            if 'open_interest' in data:
                oi = data['open_interest']
                section += f"""

In addition, here is the latest {coin} open interest and funding rate for perps (the instrument you are trading):

Open Interest: Latest: {oi.get('latest', 'N/A'):.2f} Average: {oi.get('average', 'N/A'):.2f}

Funding Rate: {data.get('funding_rate', 'N/A')}"""

            section += f"""

Intraday series (3-minute intervals, oldest → latest):

{coin} mid prices: {self._format_list(data['mid_prices'])}

EMA indicators (20-period): {self._format_list(data['ema20_series'])}

MACD indicators: {self._format_list(data['macd_series'])}

RSI indicators (7-Period): {self._format_list(data['rsi7_series'])}

RSI indicators (14-Period): {self._format_list(data['rsi14_series'])}"""

            # 添加 RSI 背离信号（如果检测到）
            if 'rsi_divergence' in data and data['rsi_divergence']['has_any_divergence']:
                div_data = data['rsi_divergence']
                section += "\n\n" + "="*70
                section += "\n⚠️ RSI 背离信号检测 - 强力反转信号\n"
                section += "="*70
                section += "\n背离是RSI指标中威力最强、也最受重视的信号，它往往预示着潜在的趋势反转。\n"
                
                # 显示每个检测到的背离信号
                for i, signal in enumerate(div_data['signals'], 1):
                    period = signal['period']
                    div_type = signal['divergence_type']
                    strength = signal['divergence_strength']
                    description = signal['description']
                    
                    # 中文翻译
                    type_cn = "顶背离 (看跌)" if div_type == "bearish" else "底背离 (看涨)"
                    strength_cn = {"strong": "强", "moderate": "中等", "weak": "弱"}[strength]
                    
                    section += f"\n[信号 {i}] {period} - {type_cn}"
                    section += f"\n  强度: {strength_cn.upper()}"
                    section += f"\n  详情: {description}"
                    
                    # # 添加交易建议
                    # if div_type == "bearish":
                    #     section += "\n  📉 建议: 考虑做空或平掉多仓，潜在下跌趋势"
                    # else:
                    #     section += "\n  📈 建议: 考虑做多或平掉空仓，潜在上涨趋势"
                
                # 多周期确认
                if div_data['multi_timeframe']:
                    section += "\n\n🔥 多周期确认: RSI(7) 和 RSI(14) 同时出现背离，信号更强！"
                
                section += "\n" + "="*70

            # 添加长期数据（如果有）
            if 'long_term' in data:
                lt = data['long_term']
                section += f"""

Longer-term context (4-hour timeframe):

20-Period EMA: {lt['ema20']:.6g} vs. 50-Period EMA: {lt['ema50']:.6g}

3-Period ATR: {lt['atr_3']:.6g} vs. 14-Period ATR: {lt['atr_14']:.6g}

Current Volume: {data['current_volume']:.3f} vs. Average Volume: {lt['avg_volume']:.3f}

MACD indicators: {self._format_list(lt['macd_series'])}

RSI indicators (14-Period): {self._format_list(lt['rsi14_series'])}"""
            
            sections.append(section)
        
        return "\n\n".join(sections)
    
    def _build_account_section(self, account_info: Dict[str, Any], positions: List[Dict[str, Any]]) -> str:
        """构建账户信息部分"""
        section = f"""HERE IS YOUR ACCOUNT INFORMATION & PERFORMANCE
Current Total Return (percent): {account_info.get('total_return_pct', 0.0):.2f}%

Available Cash: {account_info.get('available_cash', 0.0):.2f}

Current Account Value: {account_info.get('total_value', 0.0):.2f}

Current live positions & performance: """

        if positions:
            # Format positions as a space-separated string of dicts
            pos_strs = [str(pos) for pos in positions]
            section += " ".join(pos_strs)
        else:
            section += "None"

        if 'sharpe_ratio' in account_info:
            section += f"\n\nSharpe Ratio: {account_info['sharpe_ratio']:.3f}"

        return section
    
    def _format_list(self, values: List[float], decimals: int = 3) -> str:
        """格式化数字列表"""
        if not values:
            return "[]"
        formatted = [f"{v:.{decimals}f}" for v in values]
        return "[" + ", ".join(formatted) + "]"


# 测试代码
if __name__ == "__main__":
    # 测试 prompt 构建
    builder = PromptBuilder(coins=["BTC", "ETH"])
    
    # 模拟市场数据
    market_state = {
        "BTC": {
            "current_price": 107798.5,
            "current_ema20": 107919.353,
            "current_macd": 15.822,
            "current_rsi_7": 29.336,
            "current_rsi_14": 44.075,
            "mid_prices": [107979.0, 108000.0, 108072.5, 108114.0, 108057.5, 108031.0, 108002.5, 107884.5, 107830.0, 107798.5],
            "ema20_series": [107878.406, 107891.891, 107909.807, 107928.396, 107939.025, 107946.928, 107950.649, 107945.825, 107932.128, 107919.353],
            "macd_series": [52.408, 55.997, 62.958, 69.688, 68.981, 66.206, 60.405, 48.312, 30.468, 15.822],
            "rsi7_series": [62.512, 63.321, 68.597, 70.649, 58.961, 55.97, 50.045, 38.644, 29.661, 29.336],
            "rsi14_series": [61.14, 61.542, 64.201, 65.278, 60.206, 58.842, 56.106, 50.11, 44.3, 44.075],
            "current_volume": 151.082,
            "avg_volume": 4897.702,
        }
    }
    
    account_info = {
        "total_return_pct": 11.88,
        "available_cash": 4927.64,
        "total_value": 11187.63,
        "sharpe_ratio": 0.005
    }
    
    positions = [
        {
            "symbol": "BTC",
            "quantity": 0.12,
            "entry_price": 107343.0,
            "current_price": 107798.5,
            "unrealized_pnl": 54.66,
            "leverage": 10
        }
    ]
    
    prompt = builder.build_prompt(market_state, account_info, positions)
    print(prompt)
    print("\n" + "=" * 80)
    print(f"Prompt 长度: {len(prompt)} 字符")

