#!/usr/bin/env python3
"""
市场数据获取和技术指标计算模块
负责获取价格数据并计算 EMA, MACD, RSI 等指标
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any
from datetime import datetime, timedelta


class TechnicalIndicators:
    """技术指标计算类"""
    
    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> float:
        """计算指数移动平均线 (EMA)"""
        if len(prices) < period:
            return np.mean(prices)
        
        df = pd.Series(prices)
        ema = df.ewm(span=period, adjust=False).mean()
        return float(ema.iloc[-1])
    
    @staticmethod
    def calculate_ema_series(prices: List[float], period: int) -> List[float]:
        """计算 EMA 序列"""
        if len(prices) < period:
            return [np.mean(prices)] * len(prices)
        
        df = pd.Series(prices)
        ema = df.ewm(span=period, adjust=False).mean()
        return ema.tolist()
    
    @staticmethod
    def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> float:
        """计算 MACD 指标"""
        if len(prices) < slow:
            return 0.0
        
        df = pd.Series(prices)
        ema_fast = df.ewm(span=fast, adjust=False).mean()
        ema_slow = df.ewm(span=slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        return float(macd.iloc[-1])
    
    @staticmethod
    def calculate_macd_series(prices: List[float], fast: int = 12, slow: int = 26) -> List[float]:
        """计算 MACD 序列"""
        if len(prices) < slow:
            return [0.0] * len(prices)
        
        df = pd.Series(prices)
        ema_fast = df.ewm(span=fast, adjust=False).mean()
        ema_slow = df.ewm(span=slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        return macd.tolist()
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> float:
        """计算相对强弱指标 (RSI)"""
        if len(prices) < period + 1:
            return 50.0
        
        df = pd.Series(prices)
        delta = df.diff()
        
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1])
    
    @staticmethod
    def calculate_rsi_series(prices: List[float], period: int = 14) -> List[float]:
        """计算 RSI 序列"""
        if len(prices) < period + 1:
            return [50.0] * len(prices)
        
        df = pd.Series(prices)
        delta = df.diff()
        
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50.0).tolist()
    
    @staticmethod
    def calculate_atr(high: List[float], low: List[float], close: List[float], period: int = 14) -> float:
        """计算平均真实波幅 (ATR)"""
        if len(close) < 2:
            return 0.0
        
        df = pd.DataFrame({
            'high': high,
            'low': low,
            'close': close
        })
        
        df['h-l'] = df['high'] - df['low']
        df['h-pc'] = abs(df['high'] - df['close'].shift(1))
        df['l-pc'] = abs(df['low'] - df['close'].shift(1))
        
        df['tr'] = df[['h-l', 'h-pc', 'l-pc']].max(axis=1)
        atr = df['tr'].rolling(window=period).mean()
        
        return float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else 0.0
    
    @staticmethod
    def detect_rsi_divergence(prices: List[float], rsi_values: List[float], window: int = 5) -> Dict[str, Any]:
        """
        检测 RSI 背离信号
        
        Args:
            prices: 价格序列
            rsi_values: RSI 值序列
            window: 检测窗口大小
        
        Returns:
            {
                "has_divergence": bool,
                "divergence_type": "bullish" / "bearish" / None,
                "divergence_strength": "strong" / "moderate" / "weak",
                "description": str
            }
        """
        if len(prices) < window * 2 or len(rsi_values) < window * 2:
            return {
                "has_divergence": False,
                "divergence_type": None,
                "divergence_strength": None,
                "description": "数据不足"
            }
        
        # 找到局部高点和低点
        def find_peaks_and_troughs(data: List[float], window: int = 3):
            peaks = []  # (index, value)
            troughs = []  # (index, value)
            
            for i in range(window, len(data) - window):
                # 检查是否是局部高点
                if all(data[i] >= data[i-j] for j in range(1, window+1)) and \
                   all(data[i] >= data[i+j] for j in range(1, window+1)):
                    peaks.append((i, data[i]))
                
                # 检查是否是局部低点
                if all(data[i] <= data[i-j] for j in range(1, window+1)) and \
                   all(data[i] <= data[i+j] for j in range(1, window+1)):
                    troughs.append((i, data[i]))
            
            return peaks, troughs
        
        price_peaks, price_troughs = find_peaks_and_troughs(prices, window=3)
        rsi_peaks, rsi_troughs = find_peaks_and_troughs(rsi_values, window=3)
        
        # 检测顶背离 (Bearish Divergence)
        bearish_divergence = None
        if len(price_peaks) >= 2 and len(rsi_peaks) >= 2:
            # 取最后两个高点
            price_peak1, price_peak2 = price_peaks[-2], price_peaks[-1]
            
            # 找到对应的 RSI 高点
            rsi_near_peak1 = None
            rsi_near_peak2 = None
            
            for rsi_idx, rsi_val in rsi_peaks:
                if abs(rsi_idx - price_peak1[0]) <= 2:
                    rsi_near_peak1 = (rsi_idx, rsi_val)
                if abs(rsi_idx - price_peak2[0]) <= 2:
                    rsi_near_peak2 = (rsi_idx, rsi_val)
            
            if rsi_near_peak1 and rsi_near_peak2:
                price_higher = price_peak2[1] > price_peak1[1]
                rsi_lower = rsi_near_peak2[1] < rsi_near_peak1[1]
                rsi_diff = abs(rsi_near_peak1[1] - rsi_near_peak2[1])
                
                if price_higher and rsi_lower:
                    # 计算强度
                    if rsi_diff > 10:
                        strength = "strong"
                    elif rsi_diff > 5:
                        strength = "moderate"
                    else:
                        strength = "weak"
                    
                    bearish_divergence = {
                        "has_divergence": True,
                        "divergence_type": "bearish",
                        "divergence_strength": strength,
                        "description": f"价格从 {price_peak1[1]:.2f} 上涨至 {price_peak2[1]:.2f}，但 RSI 从 {rsi_near_peak1[1]:.1f} 下降至 {rsi_near_peak2[1]:.1f}，形成顶背离（RSI差异: {rsi_diff:.1f}）"
                    }
        
        # 检测底背离 (Bullish Divergence)
        bullish_divergence = None
        if len(price_troughs) >= 2 and len(rsi_troughs) >= 2:
            # 取最后两个低点
            price_trough1, price_trough2 = price_troughs[-2], price_troughs[-1]
            
            # 找到对应的 RSI 低点
            rsi_near_trough1 = None
            rsi_near_trough2 = None
            
            for rsi_idx, rsi_val in rsi_troughs:
                if abs(rsi_idx - price_trough1[0]) <= 2:
                    rsi_near_trough1 = (rsi_idx, rsi_val)
                if abs(rsi_idx - price_trough2[0]) <= 2:
                    rsi_near_trough2 = (rsi_idx, rsi_val)
            
            if rsi_near_trough1 and rsi_near_trough2:
                price_lower = price_trough2[1] < price_trough1[1]
                rsi_higher = rsi_near_trough2[1] > rsi_near_trough1[1]
                rsi_diff = abs(rsi_near_trough1[1] - rsi_near_trough2[1])
                
                if price_lower and rsi_higher:
                    # 计算强度
                    if rsi_diff > 10:
                        strength = "strong"
                    elif rsi_diff > 5:
                        strength = "moderate"
                    else:
                        strength = "weak"
                    
                    bullish_divergence = {
                        "has_divergence": True,
                        "divergence_type": "bullish",
                        "divergence_strength": strength,
                        "description": f"价格从 {price_trough1[1]:.2f} 下跌至 {price_trough2[1]:.2f}，但 RSI 从 {rsi_near_trough1[1]:.1f} 上升至 {rsi_near_trough2[1]:.1f}，形成底背离（RSI差异: {rsi_diff:.1f}）"
                    }
        
        # 返回最显著的背离
        if bearish_divergence:
            return bearish_divergence
        elif bullish_divergence:
            return bullish_divergence
        else:
            return {
                "has_divergence": False,
                "divergence_type": None,
                "divergence_strength": None,
                "description": "未检测到明显背离"
            }


class MarketDataFetcher:
    """市场数据获取类"""
    
    def __init__(self, info_api):
        self.info = info_api
        self.price_history = {}  # 存储历史价格数据
        
    def get_current_prices(self, coins: List[str]) -> Dict[str, float]:
        """获取当前价格"""
        all_mids = self.info.all_mids()
        prices = {}
        for coin in coins:
            if coin in all_mids:
                prices[coin] = float(all_mids[coin])
        return prices

    def get_top_coins_by_market_cap(self, top_n: int) -> List[str]:
        """
        按交易量获取前N个币种（使用永续合约数据）

        Args:
            top_n: 返回前N个交易量最大的币种

        Returns:
            按日交易量（dayNtlVlm USD）降序排序的币种列表
        
        注意：使用 perp (永续合约) 数据，纯按日交易量USD排序，
              确保选择流动性最好、交易最活跃的主流币种
        """
        try:
            # 获取所有活跃交易的币种
            all_mids = self.info.all_mids()
            active_coins = set(all_mids.keys())

            # 获取永续合约的元数据和资产上下文
            perp_data = self.info.meta_and_asset_ctxs()

            # perp_data[0] 包含 meta 信息（universe）
            # perp_data[1] 包含资产上下文列表
            meta = perp_data[0] if len(perp_data) > 0 else {'universe': []}
            asset_ctxs = perp_data[1] if len(perp_data) > 1 else []

            # 建立币种索引映射
            coin_names = [asset['name'] for asset in meta.get('universe', [])]

            # 收集所有币种的交易数据
            coins_with_volume = []
            
            for idx, asset_ctx in enumerate(asset_ctxs):
                try:
                    # 获取币种名称（通过索引匹配）
                    if idx >= len(coin_names):
                        continue
                    
                    coin = coin_names[idx]

                    # 只处理活跃交易的币种
                    if coin not in active_coins:
                        continue
                    
                    # 只处理支持K线数据的币种
                    if coin not in self.info.name_to_coin:
                        continue

                    # 获取交易数据
                    day_ntl_volume = float(asset_ctx.get('dayNtlVlm', 0))  # 日交易量 USD
                    open_interest = float(asset_ctx.get('openInterest', 0))  # 未平仓合约
                    mark_price = float(asset_ctx.get('markPx', 0))  # 标记价格
                    
                    # 过滤：必须有交易量
                    if day_ntl_volume > 0:
                        coin_data = {
                            'coin': coin,
                            'day_ntl_volume': day_ntl_volume,  # 日交易量（USD）
                            'open_interest': open_interest,     # 未平仓合约
                            'price': mark_price,
                        }
                        
                        coins_with_volume.append(coin_data)
                            
                except (ValueError, KeyError, IndexError) as e:
                    # 跳过数据格式错误的币种
                    continue

            # 按日交易量排序（USD）
            coins_with_volume.sort(key=lambda x: x['day_ntl_volume'], reverse=True)
            
            # 打印统计信息
            print(f"  ℹ️ 从 {len(coins_with_volume)} 个活跃 perp 币种中选择前 {top_n} 个")
            
            # 打印前几个币种的详细信息（用于调试）
            if coins_with_volume:
                print(f"  📊 Top 3: ", end="")
                for i, coin_data in enumerate(coins_with_volume[:3]):
                    print(f"{coin_data['coin']}(${coin_data['day_ntl_volume']/1e6:.1f}M)", end=" ")
                print()

            # 返回前N个币种
            top_coins = [coin_data['coin'] for coin_data in coins_with_volume[:top_n]]

            # 如果没有足够的数据，补充默认币种
            if len(top_coins) < top_n:
                default_coins = ["BTC", "ETH", "SOL", "ARB", "OP", "AVAX", "MATIC", "DOGE"]
                for default_coin in default_coins:
                    if default_coin not in top_coins and default_coin in active_coins:
                        top_coins.append(default_coin)
                        if len(top_coins) >= top_n:
                            break
            
            # 确保至少返回一些币种
            if not top_coins:
                print("  ⚠️ 未找到活跃币种，使用默认列表")
                return ["BTC", "ETH", "SOL"][:top_n]

            return top_coins[:top_n]

        except Exception as e:
            print(f"❌ 获取活跃币种失败: {e}")
            import traceback
            traceback.print_exc()
            # 返回默认币种作为fallback
            return ["BTC", "ETH", "SOL"][:top_n]
    
    def get_candles(self, coin: str, interval: str = "3m", limit: int = 100) -> List[Dict]:
        """
        获取 K 线数据
        
        Args:
            coin: 币种名称，如 "BTC"
            interval: 时间间隔，如 "3m", "1h", "4h"
            limit: 获取数量
        
        Returns:
            K线数据列表，每个元素包含 [timestamp, open, high, low, close, volume]
        """
        try:
            # 检查币种是否支持K线数据（是否在name_to_coin字典中）
            if coin not in self.info.name_to_coin:
                print(f"⚠️ 币种 {coin} 不支持K线数据，已跳过")
                return []
            
            # 计算时间范围
            # 根据 interval 和 limit 计算需要的时间范围
            from datetime import datetime, timedelta
            
            # interval 到分钟数的映射
            interval_minutes = {
                "1m": 1,
                "3m": 3,
                "5m": 5,
                "15m": 15,
                "1h": 60,
                "4h": 240,
                "1d": 1440
            }
            
            minutes = interval_minutes.get(interval, 3)
            end_time = int(datetime.now().timestamp() * 1000)  # 毫秒
            start_time = end_time - (minutes * limit * 60 * 1000)
            
            # Hyperliquid 的 candle API
            response = self.info.candles_snapshot(
                name=coin,
                interval=interval,
                startTime=start_time,
                endTime=end_time
            )
            
            if not response:
                return []
            
            # 转换为标准格式
            candles = []
            for candle in response[-limit:]:  # 只取最近的 limit 条
                candles.append({
                    'timestamp': candle['t'],
                    'open': float(candle['o']),
                    'high': float(candle['h']),
                    'low': float(candle['l']),
                    'close': float(candle['c']),
                    'volume': float(candle['v'])
                })
            
            return candles
        except Exception as e:
            print(f"获取 K 线数据失败 ({coin}): {e}")
            return []
    
    def calculate_indicators(self, candles: List[Dict], include_4h: bool = False) -> Dict[str, Any]:
        """
        计算技术指标
        
        Args:
            candles: K线数据
            include_4h: 是否包含4小时数据
        
        Returns:
            包含所有技术指标的字典
        """
        if not candles or len(candles) < 2:
            return self._empty_indicators()
        
        # 提取价格数据
        closes = [c['close'] for c in candles]
        highs = [c['high'] for c in candles]
        lows = [c['low'] for c in candles]
        volumes = [c['volume'] for c in candles]
        
        # 计算指标
        indicators = {
            'current_price': closes[-1],
            'current_ema20': TechnicalIndicators.calculate_ema(closes, 20),
            'current_macd': TechnicalIndicators.calculate_macd(closes),
            'current_rsi_7': TechnicalIndicators.calculate_rsi(closes, 7),
            'current_rsi_14': TechnicalIndicators.calculate_rsi(closes, 14),
            
            # 最近10个数据点的序列
            'mid_prices': closes[-10:],
            'ema20_series': TechnicalIndicators.calculate_ema_series(closes, 20)[-10:],
            'macd_series': TechnicalIndicators.calculate_macd_series(closes)[-10:],
            'rsi7_series': TechnicalIndicators.calculate_rsi_series(closes, 7)[-10:],
            'rsi14_series': TechnicalIndicators.calculate_rsi_series(closes, 14)[-10:],
            
            # ATR
            'atr_14': TechnicalIndicators.calculate_atr(highs, lows, closes, 14),
            
            # 成交量
            'current_volume': volumes[-1] if volumes else 0.0,
            'avg_volume': np.mean(volumes) if volumes else 0.0,
        }
        
        return indicators
    
    def get_market_state(self, coins: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        获取所有币种的完整市场状态
        
        Returns:
            {
                'BTC': {
                    'current_price': 107798.5,
                    'current_ema20': 107919.353,
                    'mid_prices': [...],
                    ...
                },
                ...
            }
        """
        market_state = {}
        
        for coin in coins:
            # 获取 3 分钟 K 线（最近 100 条）
            candles_3m = self.get_candles(coin, interval="3m", limit=100)
            
            if candles_3m:
                indicators = self.calculate_indicators(candles_3m)
                market_state[coin] = indicators
                
                # 检测 RSI 背离信号（多周期）
                mid_prices = indicators.get('mid_prices', [])
                rsi7_series = indicators.get('rsi7_series', [])
                rsi14_series = indicators.get('rsi14_series', [])
                
                # RSI(14) 背离检测
                rsi14_divergence = TechnicalIndicators.detect_rsi_divergence(
                    prices=mid_prices,
                    rsi_values=rsi14_series
                )
                
                # RSI(7) 背离检测
                rsi7_divergence = TechnicalIndicators.detect_rsi_divergence(
                    prices=mid_prices,
                    rsi_values=rsi7_series
                )
                
                # 整合背离信号
                divergence_signals = []
                
                if rsi14_divergence.get('has_divergence'):
                    divergence_signals.append({
                        'period': 'RSI(14)',
                        **rsi14_divergence
                    })
                
                if rsi7_divergence.get('has_divergence'):
                    divergence_signals.append({
                        'period': 'RSI(7)',
                        **rsi7_divergence
                    })
                
                # 添加背离信息到市场状态
                market_state[coin]['rsi_divergence'] = {
                    'has_any_divergence': len(divergence_signals) > 0,
                    'signals': divergence_signals,
                    'multi_timeframe': len(divergence_signals) > 1,  # 是否多周期确认
                }
                
                # 可选：获取 4 小时数据作为长期趋势参考
                candles_4h = self.get_candles(coin, interval="4h", limit=50)
                if candles_4h:
                    closes_4h = [c['close'] for c in candles_4h]
                    highs_4h = [c['high'] for c in candles_4h]
                    lows_4h = [c['low'] for c in candles_4h]
                    volumes_4h = [c['volume'] for c in candles_4h]
                    
                    market_state[coin]['long_term'] = {
                        'ema20': TechnicalIndicators.calculate_ema(closes_4h, 20),
                        'ema50': TechnicalIndicators.calculate_ema(closes_4h, 50),
                        'atr_3': TechnicalIndicators.calculate_atr(highs_4h, lows_4h, closes_4h, 3),
                        'atr_14': TechnicalIndicators.calculate_atr(highs_4h, lows_4h, closes_4h, 14),
                        'avg_volume': np.mean(volumes_4h),
                        'macd_series': TechnicalIndicators.calculate_macd_series(closes_4h)[-10:],
                        'rsi14_series': TechnicalIndicators.calculate_rsi_series(closes_4h, 14)[-10:],
                    }
        
        return market_state
    
    def _empty_indicators(self) -> Dict[str, Any]:
        """返回空指标"""
        return {
            'current_price': 0.0,
            'current_ema20': 0.0,
            'current_macd': 0.0,
            'current_rsi_7': 50.0,
            'current_rsi_14': 50.0,
            'mid_prices': [],
            'ema20_series': [],
            'macd_series': [],
            'rsi7_series': [],
            'rsi14_series': [],
            'atr_14': 0.0,
            'current_volume': 0.0,
            'avg_volume': 0.0,
        }


# 测试代码
if __name__ == "__main__":
    # 测试指标计算
    test_prices = [100, 102, 101, 105, 107, 106, 108, 110, 109, 111, 113, 112, 115, 117, 116]
    
    print("测试技术指标计算:")
    print(f"价格序列: {test_prices}")
    print(f"EMA(20): {TechnicalIndicators.calculate_ema(test_prices, 20):.2f}")
    print(f"MACD: {TechnicalIndicators.calculate_macd(test_prices):.3f}")
    print(f"RSI(7): {TechnicalIndicators.calculate_rsi(test_prices, 7):.2f}")
    print(f"RSI(14): {TechnicalIndicators.calculate_rsi(test_prices, 14):.2f}")

