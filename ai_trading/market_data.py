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

