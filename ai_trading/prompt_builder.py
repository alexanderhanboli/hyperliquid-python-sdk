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
    
    def build_prompt(
        self,
        market_state: Dict[str, Dict[str, Any]],
        account_info: Dict[str, Any],
        positions: List[Dict[str, Any]]
    ) -> str:
        """
        构建完整的 AI prompt
        
        Args:
            market_state: 市场数据和技术指标
            account_info: 账户信息（现金、总价值等）
            positions: 当前持仓列表
        
        Returns:
            格式化的 prompt 字符串
        """
        self.invocation_count += 1
        elapsed_minutes = int((datetime.now() - self.start_time).total_seconds() / 60)
        
        prompt_parts = [
            self._build_header(elapsed_minutes),
            self._build_market_state_section(market_state),
            self._build_account_section(account_info, positions),
            self._build_instructions_section()
        ]
        
        return "\n\n".join(prompt_parts)
    
    def _build_header(self, elapsed_minutes: int) -> str:
        """构建 prompt 头部"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return f"""USER_PROMPT
It has been {elapsed_minutes} minutes since you started trading. The current time is {current_time} and you've been invoked {self.invocation_count} times. Below, we are providing you with a variety of state data, price data, and predictive signals so you can discover alpha. Below that is your current account information, value, performance, positions, etc.

ALL OF THE PRICE OR SIGNAL DATA BELOW IS ORDERED: OLDEST → NEWEST

Timeframes note: Unless stated otherwise in a section title, intraday series are provided at 3-minute intervals. If a coin uses a different interval, it is explicitly stated in that coin's section.

CURRENT MARKET STATE FOR ALL COINS"""
    
    def _build_market_state_section(self, market_state: Dict[str, Dict[str, Any]]) -> str:
        """构建市场状态部分"""
        sections = []
        
        for coin in self.coins:
            if coin not in market_state:
                continue
            
            data = market_state[coin]
            
            section = f"""ALL {coin} DATA
current_price = {data['current_price']:.6g}, current_ema20 = {data['current_ema20']:.6g}, current_macd = {data['current_macd']:.6g}, current_rsi (7 period) = {data['current_rsi_7']:.3f}

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
                    
                    # 添加交易建议
                    if div_type == "bearish":
                        section += "\n  📉 建议: 考虑做空或平掉多仓，潜在下跌趋势"
                    else:
                        section += "\n  📈 建议: 考虑做多或平掉空仓，潜在上涨趋势"
                
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

Current Account Value: {account_info.get('total_value', 0.0):.2f}"""
        
        if positions:
            section += "\n\nCurrent live positions & performance:"
            for pos in positions:
                pos_str = str(pos)
                section += f" {pos_str}"
        else:
            section += "\n\nNo current positions."
        
        if 'sharpe_ratio' in account_info:
            section += f"\n\nSharpe Ratio: {account_info['sharpe_ratio']:.3f}"
        
        return section
    
    def _build_instructions_section(self) -> str:
        """构建指令部分"""
        return """INSTRUCTIONS:
Based on the market data above, make your trading decisions. For each coin, you can:
1. ENTRY - Enter a new position (if you have no position)
2. HOLD - Keep your current position
3. CLOSE - Close your current position

⚠️ PROFESSIONAL TRADER MINDSET - PATIENCE IS KEY:
You are a mature, professional trader. Professional traders do NOT trade every opportunity.
- Wait for HIGH-QUALITY setups with strong confluence of signals
- It is PERFECTLY FINE to stay in cash and do nothing if conditions are unclear
- "No trade" is often the best trade - preserve capital when edge is uncertain
- Only enter when you have genuine conviction based on multiple confirming indicators
- Overtrading is the enemy - be selective and disciplined
- Better to miss an opportunity than to force a mediocre trade

Good entry signals typically show:
✓ Multiple indicators confirming the same direction (RSI, MACD, EMA alignment)
✓ Strong divergence signals (especially multi-timeframe confirmation)
✓ Clear trend or momentum with favorable risk/reward (≥1:2)
✓ Volume confirmation for breakouts
✓ Price action near key levels (support/resistance)

Avoid trading when:
✗ Indicators are mixed or contradictory
✗ Market is choppy/sideways with no clear trend
✗ Risk/reward ratio is poor (<1:2)
✗ You're uncertain or forcing a trade just to "do something"

Remember: A professional trader's job is to wait for the best opportunities, not to be constantly active.

Return your decisions in the following JSON format:

For ENTRY:
{
  "COIN": {
    "trade_signal_args": {
      "coin": "COIN",
      "signal": "entry",
      "is_buy": true/false,
      "quantity": <float>,
      "profit_target": <float>,
      "stop_loss": <float>,
      "invalidation_condition": "<string>",
      "leverage": <int 5-40>,
      "confidence": <0-1>,
      "risk_usd": <float>,
      "justification": "<1-4 sentences>"
    }
  }
}

For HOLD:
{
  "COIN": {
    "trade_signal_args": {
      "coin": "COIN",
      "signal": "hold",
      "quantity": <full current size>,
      "profit_target": <float>,
      "stop_loss": <float>,
      "invalidation_condition": "<string>",
      "leverage": <int>,
      "confidence": <0-1>,
      "risk_usd": <float>
    }
  }
}

For CLOSE:
{
  "COIN": {
    "trade_signal_args": {
      "coin": "COIN",
      "signal": "close",
      "quantity": <full position size>,
      "justification": "<1-4 sentences>"
    }
  }
}

IMPORTANT RULES:
1. No pyramiding - you cannot add to existing positions
2. Always set stop loss and take profit for entries
3. Leverage range: 5x to 40x
4. Risk/reward ratio must be at least 1:2 (prefer 1:2.5 or 1:3 when possible)

STOP LOSS & TAKE PROFIT - ATR-BASED APPROACH:
Use ATR (Average True Range) to set intelligent stops/targets that adapt to market volatility:

Formula:
- STOP LOSS: Entry ± (1.5 to 2.0) × 14-Period ATR  →  typically 1.5%-3% from entry
- TAKE PROFIT: Entry ± (3.0 to 4.0) × 14-Period ATR  →  typically 4%-6% from entry

Example: BNB at $1000, ATR = $20
- LONG: Stop $960 (-2×ATR), Target $1080 (+4×ATR) = 4% risk, 8% profit = 1:2 ✅
- SHORT: Stop $1040 (+2×ATR), Target $920 (-4×ATR) = 4% risk, 8% profit = 1:2 ✅

Position Sizing:
Position Size = risk_usd / (entry_price × stop_loss_percent)
Example: $20 risk, 2% stop, $1000 BNB → Size = 20/(1000×0.02) = 1.0 BNB

Please analyze the data and return your trading decisions in valid JSON format."""
    
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

