#!/usr/bin/env python3
"""
订单执行器
根据 AI 的决策执行交易订单，包括开仓、平仓、设置止盈止损
"""

from typing import Dict, Any, Optional, List
import time


class OrderExecutor:
    """订单执行器"""
    
    def __init__(self, exchange, info_api, min_order_value: float = 10.0):
        """
        Args:
            exchange: Hyperliquid Exchange 实例
            info_api: Hyperliquid Info 实例
            min_order_value: 最小订单价值（USD）
        """
        self.exchange = exchange
        self.info = info_api
        self.min_order_value = min_order_value
        self.positions = {}  # 存储持仓信息
    
    def execute_decision(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行 AI 的交易决策
        
        Args:
            decision: AI 返回的决策，格式如：
            {
                "coin": "BTC",
                "signal": "entry/hold/close",
                "is_buy": True,
                "quantity": 0.1,
                "profit_target": 110000,
                "stop_loss": 105000,
                "leverage": 10,
                ...
            }
        
        Returns:
            执行结果
        """
        signal = decision.get("signal", "").lower()
        coin = decision.get("coin", "")
        
        if not coin:
            return {"status": "error", "message": "Missing coin"}
        
        try:
            if signal == "entry":
                return self._execute_entry(decision)
            elif signal == "hold":
                return self._execute_hold(decision)
            elif signal == "close":
                return self._execute_close(decision)
            else:
                return {"status": "error", "message": f"Unknown signal: {signal}"}
        
        except Exception as e:
            return {"status": "error", "message": f"Execution failed: {str(e)}"}
    
    def _execute_entry(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """执行开仓"""
        coin = decision["coin"]
        is_buy = decision.get("is_buy", True)
        quantity = decision.get("quantity", 0.0)
        leverage = decision.get("leverage", 10)
        stop_loss = decision.get("stop_loss")
        profit_target = decision.get("profit_target")
        
        # 验证参数
        if quantity <= 0:
            return {"status": "error", "message": "Invalid quantity"}
        
        # 获取当前价格
        all_mids = self.info.all_mids()
        current_price = float(all_mids.get(coin, 0))
        
        if current_price <= 0:
            return {"status": "error", "message": f"Cannot get price for {coin}"}
        
        # 检查订单价值
        order_value = quantity * current_price / leverage
        if order_value < self.min_order_value:
            return {
                "status": "skipped",
                "message": f"Order value ${order_value:.2f} below minimum ${self.min_order_value}"
            }
        
        print(f"\n{'='*60}")
        print(f"📈 开仓: {coin}")
        print(f"  方向: {'做多 (Long)' if is_buy else '做空 (Short)'}")
        print(f"  数量: {quantity}")
        print(f"  当前价格: ${current_price:.2f}")
        print(f"  杠杆: {leverage}x")
        print(f"  保证金: ${order_value:.2f}")
        if stop_loss:
            print(f"  止损价: ${stop_loss:.2f}")
        if profit_target:
            print(f"  止盈价: ${profit_target:.2f}")
        print(f"{'='*60}")
        
        # 1. 设置杠杆
        try:
            leverage_result = self.exchange.update_leverage(leverage, coin)
            print(f"✅ 杠杆设置: {leverage}x")
        except Exception as e:
            print(f"⚠️ 杠杆设置失败: {e}")
        
        # 2. 市价开仓
        try:
            slippage = 0.01  # 1% 滑点容忍
            entry_result = self.exchange.market_open(
                coin=coin,
                is_buy=is_buy,
                sz=quantity,
                slippage=slippage
            )
            
            if entry_result.get("status") != "ok":
                return {
                    "status": "error",
                    "message": f"Entry order failed: {entry_result}"
                }
            
            print(f"✅ 开仓成功")
            
            # 等待成交
            time.sleep(1)
            
            # 获取实际成交价
            user_state = self.info.user_state(self.exchange.wallet.address)
            actual_entry_price = current_price
            
            if user_state and 'assetPositions' in user_state:
                for pos in user_state['assetPositions']:
                    if pos['position']['coin'] == coin:
                        actual_entry_price = float(pos['position']['entryPx'])
                        break
            
            print(f"  实际成交价: ${actual_entry_price:.2f}")
            
            # 3. 设置止损止盈
            sl_oid = None
            tp_oid = None
            
            if stop_loss:
                sl_result = self._set_stop_loss(
                    coin=coin,
                    is_buy=is_buy,
                    quantity=quantity,
                    stop_loss_price=stop_loss
                )
                if sl_result.get("status") == "ok":
                    sl_oid = sl_result.get("order_id")
                    print(f"✅ 止损已设置: ${stop_loss:.2f} (OID: {sl_oid})")
                else:
                    print(f"⚠️ 止损设置失败: {sl_result.get('message')}")
            
            if profit_target:
                tp_result = self._set_take_profit(
                    coin=coin,
                    is_buy=is_buy,
                    quantity=quantity,
                    take_profit_price=profit_target
                )
                if tp_result.get("status") == "ok":
                    tp_oid = tp_result.get("order_id")
                    print(f"✅ 止盈已设置: ${profit_target:.2f} (OID: {tp_oid})")
                else:
                    print(f"⚠️ 止盈设置失败: {tp_result.get('message')}")
            
            # 记录持仓
            self.positions[coin] = {
                "coin": coin,
                "is_buy": is_buy,
                "quantity": quantity,
                "entry_price": actual_entry_price,
                "leverage": leverage,
                "stop_loss": stop_loss,
                "profit_target": profit_target,
                "sl_oid": sl_oid,
                "tp_oid": tp_oid,
                "entry_time": time.time()
            }
            
            return {
                "status": "ok",
                "action": "entry",
                "coin": coin,
                "entry_price": actual_entry_price,
                "sl_oid": sl_oid,
                "tp_oid": tp_oid
            }
        
        except Exception as e:
            return {"status": "error", "message": f"Entry execution failed: {str(e)}"}
    
    def _execute_hold(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """执行持仓（不做任何操作）"""
        coin = decision["coin"]
        
        # 可以在这里更新止盈止损，但通常 hold 表示保持不变
        print(f"📊 持仓: {coin} - 保持当前仓位")
        
        return {
            "status": "ok",
            "action": "hold",
            "coin": coin
        }
    
    def _execute_close(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """执行平仓"""
        coin = decision["coin"]
        quantity = decision.get("quantity", 0.0)
        
        if quantity <= 0:
            return {"status": "error", "message": "Invalid quantity for close"}
        
        print(f"\n{'='*60}")
        print(f"📉 平仓: {coin}")
        print(f"  数量: {quantity}")
        print(f"{'='*60}")
        
        try:
            # 市价平仓
            slippage = 0.01
            close_result = self.exchange.market_close(
                coin=coin,
                sz=quantity,
                slippage=slippage
            )
            
            if close_result.get("status") != "ok":
                return {
                    "status": "error",
                    "message": f"Close order failed: {close_result}"
                }
            
            print(f"✅ 平仓成功")
            
            # 取消相关的止损止盈订单
            if coin in self.positions:
                pos = self.positions[coin]
                if pos.get("sl_oid"):
                    try:
                        self.exchange.cancel(coin, pos["sl_oid"])
                        print(f"✅ 止损订单已取消")
                    except:
                        pass
                
                if pos.get("tp_oid"):
                    try:
                        self.exchange.cancel(coin, pos["tp_oid"])
                        print(f"✅ 止盈订单已取消")
                    except:
                        pass
                
                # 移除持仓记录
                del self.positions[coin]
            
            return {
                "status": "ok",
                "action": "close",
                "coin": coin
            }
        
        except Exception as e:
            return {"status": "error", "message": f"Close execution failed: {str(e)}"}
    
    def _set_stop_loss(
        self,
        coin: str,
        is_buy: bool,
        quantity: float,
        stop_loss_price: float
    ) -> Dict[str, Any]:
        """设置止损单"""
        try:
            result = self.exchange.order(
                name=coin,
                is_buy=not is_buy,  # 止损方向与持仓相反
                sz=quantity,
                limit_px=stop_loss_price * (0.99 if is_buy else 1.01),  # 稍微激进一点
                order_type={
                    "trigger": {
                        "triggerPx": stop_loss_price,
                        "isMarket": True,
                        "tpsl": "sl"
                    }
                },
                reduce_only=True
            )
            
            if result.get("status") == "ok":
                status = result["response"]["data"]["statuses"][0]
                if "resting" in status:
                    return {
                        "status": "ok",
                        "order_id": status["resting"]["oid"]
                    }
            
            return {"status": "error", "message": str(result)}
        
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _set_take_profit(
        self,
        coin: str,
        is_buy: bool,
        quantity: float,
        take_profit_price: float
    ) -> Dict[str, Any]:
        """设置止盈单"""
        try:
            result = self.exchange.order(
                name=coin,
                is_buy=not is_buy,  # 止盈方向与持仓相反
                sz=quantity,
                limit_px=take_profit_price * (1.01 if is_buy else 0.99),
                order_type={
                    "trigger": {
                        "triggerPx": take_profit_price,
                        "isMarket": True,
                        "tpsl": "tp"
                    }
                },
                reduce_only=True
            )
            
            if result.get("status") == "ok":
                status = result["response"]["data"]["statuses"][0]
                if "resting" in status:
                    return {
                        "status": "ok",
                        "order_id": status["resting"]["oid"]
                    }
            
            return {"status": "error", "message": str(result)}
        
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_current_positions(self) -> List[Dict[str, Any]]:
        """获取当前持仓"""
        try:
            user_state = self.info.user_state(self.exchange.wallet.address)
            
            if not user_state or 'assetPositions' not in user_state:
                return []
            
            positions = []
            for asset_pos in user_state['assetPositions']:
                pos = asset_pos['position']
                coin = pos['coin']
                
                # 解析持仓信息
                size = abs(float(pos['szi']))
                if size > 0:
                    entry_price = float(pos['entryPx'])
                    mark_price = float(pos.get('markPx', entry_price))
                    unrealized_pnl = float(pos.get('unrealizedPnl', 0))
                    leverage = int(pos.get('leverage', {}).get('value', 1))
                    liquidation_px = float(pos.get('liquidationPx', 0))
                    
                    position_info = {
                        "coin": coin,
                        "quantity": size,
                        "is_buy": float(pos['szi']) > 0,
                        "entry_price": entry_price,
                        "current_price": mark_price,
                        "unrealized_pnl": unrealized_pnl,
                        "leverage": leverage,
                        "liquidation_price": liquidation_px,
                    }
                    
                    # 添加我们记录的额外信息
                    if coin in self.positions:
                        stored = self.positions[coin]
                        position_info.update({
                            "stop_loss": stored.get("stop_loss"),
                            "profit_target": stored.get("profit_target"),
                            "sl_oid": stored.get("sl_oid"),
                            "tp_oid": stored.get("tp_oid"),
                        })
                    
                    positions.append(position_info)
            
            return positions
        
        except Exception as e:
            print(f"获取持仓失败: {e}")
            return []
    
    def get_account_value(self) -> Dict[str, float]:
        """获取账户价值"""
        try:
            user_state = self.info.user_state(self.exchange.wallet.address)
            
            if not user_state:
                return {
                    "total_value": 0.0,
                    "available_cash": 0.0,
                    "total_margin": 0.0
                }
            
            # 从 marginSummary 获取信息
            margin_summary = user_state.get('marginSummary', {})
            account_value = float(margin_summary.get('accountValue', 0))
            total_margin = float(margin_summary.get('totalMarginUsed', 0))
            
            return {
                "total_value": account_value,
                "available_cash": account_value - total_margin,
                "total_margin": total_margin
            }
        
        except Exception as e:
            print(f"获取账户价值失败: {e}")
            return {
                "total_value": 0.0,
                "available_cash": 0.0,
                "total_margin": 0.0
            }


if __name__ == "__main__":
    print("OrderExecutor 模块")
    print("此模块需要与 Hyperliquid Exchange 实例配合使用")

