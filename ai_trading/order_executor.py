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

        # 同步现有持仓到本地跟踪（处理重启后的情况）
        self._sync_positions_from_exchange()
    
    def _round_price(self, coin: str, price: float) -> float:
        """
        根据币种的 tick size 舍入价格
        参考 Hyperliquid SDK 的 rounding 示例
        价格最多5位有效数字，最多 max_decimals - szDecimals 位小数
        """
        # 价格大于100k时直接取整
        if price > 100_000:
            return round(price)
        
        asset = self.info.coin_to_asset[coin]
        # spot assets start at 10000
        is_spot = asset >= 10_000
        max_decimals = 8 if is_spot else 6
        sz_decimals = self.info.asset_to_sz_decimals[asset]
        
        # 舍入到 5 位有效数字，然后限制小数位数
        return round(float(f"{price:.5g}"), max_decimals - sz_decimals)
    
    def _round_size(self, coin: str, size: float) -> float:
        """
        根据币种的 szDecimals 舍入订单大小
        
        Args:
            coin: 币种名称
            size: 原始订单大小
            
        Returns:
            舍入后的订单大小
        """
        asset = self.info.coin_to_asset[coin]
        sz_decimals = self.info.asset_to_sz_decimals[asset]
        return round(size, sz_decimals)
    
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

    def _validate_tp_sl_params(self, decision: Dict[str, Any]) -> bool:
        """
        验证止损止盈参数的有效性

        Args:
            decision: 交易决策

        Returns:
            True 如果参数有效，False 否则
        """
        coin = decision.get("coin", "")
        stop_loss = decision.get("stop_loss")
        profit_target = decision.get("profit_target")
        is_buy = decision.get("is_buy", True)

        # 获取当前价格
        all_mids = self.info.all_mids()
        current_price = float(all_mids.get(coin, 0))

        if current_price <= 0:
            return False

        # 如果设置了止损，验证其合理性
        if stop_loss is not None:
            if is_buy and stop_loss >= current_price:
                # 做多时，止损价应该低于当前价
                return False
            elif not is_buy and stop_loss <= current_price:
                # 做空时，止损价应该高于当前价
                return False

        # 如果设置了止盈，验证其合理性
        if profit_target is not None:
            if is_buy and profit_target <= current_price:
                # 做多时，止盈价应该高于当前价
                return False
            elif not is_buy and profit_target >= current_price:
                # 做空时，止盈价应该低于当前价
                return False

        return True

    def _execute_entry(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行开仓 - 必须止损止盈都设置成功才保留仓位

        CRITICAL: Every entry MUST have both stop_loss and profit_target.
        If either TP or SL setup fails, the position will be emergency-closed.
        """
        coin = decision["coin"]
        is_buy = decision.get("is_buy", True)
        quantity = decision.get("quantity", 0.0)
        leverage = decision.get("leverage", 10)
        stop_loss = decision.get("stop_loss")
        profit_target = decision.get("profit_target")

        # 🔒 CRITICAL: Validate that both TP and SL are provided
        if stop_loss is None or profit_target is None:
            return {
                "status": "error",
                "message": f"ENTRY requires both stop_loss and profit_target. Got SL={stop_loss}, TP={profit_target}"
            }

        # 验证基础参数
        if quantity <= 0:
            return {"status": "error", "message": "Invalid quantity"}

        # 获取当前价格
        all_mids = self.info.all_mids()
        current_price = float(all_mids.get(coin, 0))

        if current_price <= 0:
            return {"status": "error", "message": f"Cannot get price for {coin}"}

        # 检查订单价值（使用名义价值，而不是保证金）
        notional_value = quantity * current_price  # 实际仓位价值
        margin_required = notional_value / leverage  # 所需保证金

        # Hyperliquid 最小订单要求通常是基于名义价值（$10）
        if notional_value < self.min_order_value:
            return {
                "status": "skipped",
                "message": f"Position value ${notional_value:.2f} below minimum ${self.min_order_value} (margin would be ${margin_required:.2f} at {leverage}x)"
            }

        # 🔒 资金充足性检查 - 防止保证金不足
        account_info = self.get_account_value()
        available_cash = account_info['available_cash']
        total_value = account_info['total_value']
        
        # 检查可用资金是否为负（高风险状态）
        if available_cash < 0:
            print(f"🚨 警告: 可用资金为负 ${available_cash:.2f}，账户处于高风险状态！")
            return {
                "status": "error",
                "message": f"Account at risk: available cash is negative ${available_cash:.2f}. Cannot open new positions."
            }
        
        # 检查保证金使用率（不应超过80%）- 已包含资金充足性和安全边际检查
        total_margin_after = account_info['total_margin'] + margin_required
        margin_usage_ratio = (total_margin_after / total_value) if total_value > 0 else 1.0

        if margin_usage_ratio > 0.8:
            print(f"⚠️ 保证金使用率过高: {margin_usage_ratio*100:.1f}% (需要 ${margin_required:.2f}，可用 ${available_cash:.2f})")
            return {
                "status": "error",
                "message": f"Margin usage too high: {margin_usage_ratio*100:.1f}% (max 80%)"
            }

        # 验证止损止盈参数的有效性
        if not self._validate_tp_sl_params(decision):
            return {"status": "error", "message": "Invalid stop loss or take profit parameters"}

        # 舍入数量以符合 szDecimals
        rounded_quantity = self._round_size(coin, quantity)
        
        print(f"\n{'='*60}")
        print(f"📈 开仓: {coin}")
        print(f"  方向: {'做多 (Long)' if is_buy else '做空 (Short)'}")
        print(f"  数量: {rounded_quantity}")
        print(f"  当前价格: ${current_price:.2f}")
        print(f"  杠杆: {leverage}x")
        print(f"  仓位价值: ${notional_value:.2f}")
        print(f"  所需保证金: ${margin_required:.2f}")
        if stop_loss:
            print(f"  止损价: ${stop_loss:.2f}")
        if profit_target:
            print(f"  止盈价: ${profit_target:.2f}")
        print(f"{'='*60}")

        # 0. 清理该币种的所有挂单（防止孤立的 TP/SL 订单）
        self._cancel_all_orders_for_coin(coin)

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
                name=coin,  # 注意参数名是 'name' 不是 'coin'
                is_buy=is_buy,
                sz=rounded_quantity,
                px=None,  # 价格参数（None 表示使用 slippage 调整的中间价）
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

            # 获取实际成交价并验证持仓是否存在
            user_state = self.info.user_state(self.exchange.wallet.address)
            actual_entry_price = current_price
            position_found = False

            if user_state and 'assetPositions' in user_state:
                for pos in user_state['assetPositions']:
                    if pos['position']['coin'] == coin:
                        actual_entry_price = float(pos['position']['entryPx'])
                        actual_size = abs(float(pos['position'].get('szi', 0)))
                        position_found = True
                        print(f"  实际成交价: ${actual_entry_price:.2f}")
                        print(f"  实际仓位大小: {actual_size}")
                        break

            if not position_found:
                print(f"⚠️ 警告: 订单返回成功但未找到持仓！")
                print(f"   可能原因: 订单价值过小被拒绝，或成交后立即被清算")
                print(f"   订单详情: {entry_result}")
                return {
                    "status": "error",
                    "message": f"Order accepted but no position found. Notional: ${notional_value:.2f}, Margin: ${margin_required:.2f}"
                }

            # 3. 设置止损止盈 - 必须都成功，否则立即平仓
            # Set stop loss
            sl_result = self._set_stop_loss(
                coin=coin,
                is_buy=is_buy,
                quantity=rounded_quantity,
                stop_loss_price=stop_loss
            )

            if sl_result.get("status") != "ok":
                print(f"❌ 止损设置失败: {sl_result.get('message')}")
                print(f"🚨 执行紧急平仓")
                self._emergency_close(coin, rounded_quantity)
                return {"status": "error", "message": f"Stop loss setup failed: {sl_result.get('message')}"}

            sl_oid = sl_result.get("order_id")
            print(f"✅ 止损已设置: ${stop_loss:.2f} (OID: {sl_oid})")

            # Set take profit
            tp_result = self._set_take_profit(
                coin=coin,
                is_buy=is_buy,
                quantity=rounded_quantity,
                take_profit_price=profit_target
            )

            if tp_result.get("status") != "ok":
                print(f"❌ 止盈设置失败: {tp_result.get('message')}")
                print(f"�� 取消止损订单并执行紧急平仓")
                self._cancel_orders(coin, sl_oid=sl_oid, tp_oid=None)
                self._emergency_close(coin, rounded_quantity)
                return {"status": "error", "message": f"Take profit setup failed: {tp_result.get('message')}"}

            tp_oid = tp_result.get("order_id")
            print(f"✅ 止盈已设置: ${profit_target:.2f} (OID: {tp_oid})")

            # 记录持仓
            self.positions[coin] = {
                "coin": coin,
                "is_buy": is_buy,
                "quantity": rounded_quantity,
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

    def _cancel_orders(self, coin: str, sl_oid: Optional[int] = None, tp_oid: Optional[int] = None):
        """
        取消止损止盈订单的统一方法

        Args:
            coin: 币种
            sl_oid: 止损订单ID
            tp_oid: 止盈订单ID
        """
        if sl_oid:
            try:
                self.exchange.cancel(coin, sl_oid)
                print(f"✅ 已取消止损订单: {sl_oid}")
            except:
                pass

        if tp_oid:
            try:
                self.exchange.cancel(coin, tp_oid)
                print(f"✅ 已取消止盈订单: {tp_oid}")
            except:
                pass

    def _cancel_all_orders_for_coin(self, coin: str):
        """
        取消某个币种的所有挂单

        这个方法用于清理孤立的 TP/SL 订单。在开仓前调用，
        确保没有旧的订单残留（例如重启后或手动交易后）。

        Args:
            coin: 币种
        """
        try:
            # 获取该币种的所有未成交订单
            open_orders = self.info.open_orders(self.exchange.wallet.address)

            if not open_orders:
                return

            coin_orders = [o for o in open_orders if o.get("coin") == coin]

            if coin_orders:
                print(f"  🧹 发现 {coin} 有 {len(coin_orders)} 个未成交订单，正在清理...")
                for order in coin_orders:
                    try:
                        oid = order.get("oid")
                        self.exchange.cancel(coin, oid)
                        print(f"     ✅ 已取消订单 {oid}")
                    except Exception as e:
                        print(f"     ⚠️ 取消订单 {oid} 失败: {e}")

        except Exception as e:
            print(f"  ⚠️ 获取未成交订单失败: {e}")
    
    def _emergency_close(self, coin: str, quantity: float) -> Dict[str, Any]:
        """
        紧急平仓方法 - 当止损止盈设置失败时立即平仓

        Args:
            coin: 币种
            quantity: 平仓数量

        Returns:
            平仓结果
        """
        print(f"🚨 紧急平仓: {coin} - 数量: {quantity}")

        try:
            # 使用位置参数: coin, sz, px, slippage
            close_result = self.exchange.market_close(coin, quantity, None, 0.05)

            if close_result is None:
                print(f"❌ 紧急平仓失败: 未找到持仓或无法平仓")
                return {"status": "error", "message": "Emergency close failed: Position not found"}
            
            if close_result.get("status") == "ok":
                print(f"✅ 紧急平仓成功")
                return {"status": "ok", "message": "Emergency close successful"}
            
            print(f"❌ 紧急平仓失败: {close_result}")
            return {"status": "error", "message": f"Emergency close failed: {close_result}"}

        except Exception as e:
            print(f"❌ 紧急平仓异常: {str(e)}")
            return {"status": "error", "message": f"Emergency close exception: {str(e)}"}

    def _execute_hold(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行持仓（不做任何操作）

        NOTE: HOLD signal means keep the current position unchanged.
        The AI is required to include TP/SL in HOLD decisions for tracking,
        but we don't modify the existing TP/SL orders here.

        The existing TP/SL orders remain active and will trigger automatically
        when price reaches those levels.
        """
        coin = decision["coin"]

        print(f"📊 持仓: {coin} - 保持当前仓位")

        # Log the AI's current TP/SL view (for debugging)
        if "profit_target" in decision or "stop_loss" in decision:
            print(f"   AI 维持 TP/SL: TP=${decision.get('profit_target', 'N/A')} SL=${decision.get('stop_loss', 'N/A')}")

        return {
            "status": "ok",
            "action": "hold",
            "coin": coin
        }
    
    def _execute_close(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行平仓

        CRITICAL: When closing a position, this function:
        1. Closes the position via market order
        2. Cancels associated TP/SL orders
        3. Removes position from tracking

        This ensures no orphaned TP/SL orders remain after exit.
        """
        coin = decision["coin"]
        quantity = decision.get("quantity")  # 可以为 None，让 market_close 自动平所有仓位

        print(f"\n{'='*60}")
        print(f"📉 平仓: {coin}")
        if quantity:
            print(f"  数量: {quantity}")
        else:
            print(f"  数量: 全部持仓")
        print(f"{'='*60}")

        try:
            # 市价平仓 - 使用位置参数: coin, sz, px, slippage
            slippage = 0.01
            close_result = self.exchange.market_close(coin, quantity, None, slippage)
            
            # market_close 可能返回 None（没有找到持仓）
            if close_result is None:
                print(f"❌ 平仓失败: 未找到持仓")
                return {"status": "error", "message": "No position found to close"}
            
            if close_result.get("status") != "ok":
                return {
                    "status": "error",
                    "message": f"Close order failed: {close_result}"
                }
            
            print(f"✅ 平仓成功")

            # 取消相关的止损止盈订单
            if coin in self.positions:
                pos = self.positions[coin]
                sl_oid = pos.get("sl_oid")
                tp_oid = pos.get("tp_oid")

                if sl_oid or tp_oid:
                    print(f"  取消关联的 TP/SL 订单...")
                    self._cancel_orders(coin, sl_oid, tp_oid)
                else:
                    # 重启后的持仓，我们没有订单 ID，需要查询并取消
                    print(f"  ⚠️ 无 TP/SL 订单 ID (可能是重启后的持仓)，清理所有挂单...")
                    self._cancel_all_orders_for_coin(coin)

                # 移除持仓记录
                del self.positions[coin]
            else:
                # 这种情况理论上不应该发生（因为 _sync_positions_from_exchange）
                print(f"  ⚠️ 警告: {coin} 不在本地跟踪中，尝试清理挂单...")
                self._cancel_all_orders_for_coin(coin)

            return {
                "status": "ok",
                "action": "close",
                "coin": coin
            }
        
        except Exception as e:
            return {"status": "error", "message": f"Close execution failed: {str(e)}"}
    
    def _set_tp_sl_order(
        self,
        coin: str,
        is_buy: bool,
        quantity: float,
        trigger_price: float,
        order_type_flag: str  # "sl" 或 "tp"
    ) -> Dict[str, Any]:
        """
        统一的止盈止损订单设置方法
        
        Args:
            coin: 币种
            is_buy: 持仓是否为做多
            quantity: 订单数量
            trigger_price: 触发价格
            order_type_flag: "sl" (止损) 或 "tp" (止盈)
        """
        try:
            # 舍入价格以符合 tick size
            rounded_trigger = self._round_price(coin, trigger_price)
            # 止损用更宽松的limit价格，止盈用更保守的limit价格
            multiplier = 0.99 if (order_type_flag == "sl" and is_buy) or (order_type_flag == "tp" and not is_buy) else 1.01
            rounded_limit_px = self._round_price(coin, trigger_price * multiplier)
            # 舍入订单数量以符合 szDecimals
            rounded_quantity = self._round_size(coin, quantity)
            
            result = self.exchange.order(
                name=coin,
                is_buy=not is_buy,  # 平仓方向与持仓相反
                sz=rounded_quantity,
                limit_px=rounded_limit_px,
                order_type={
                    "trigger": {
                        "triggerPx": rounded_trigger,
                        "isMarket": True,
                        "tpsl": order_type_flag
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
    
    def _set_stop_loss(
        self,
        coin: str,
        is_buy: bool,
        quantity: float,
        stop_loss_price: float
    ) -> Dict[str, Any]:
        """设置止损单"""
        return self._set_tp_sl_order(coin, is_buy, quantity, stop_loss_price, "sl")
    
    def _set_take_profit(
        self,
        coin: str,
        is_buy: bool,
        quantity: float,
        take_profit_price: float
    ) -> Dict[str, Any]:
        """设置止盈单"""
        return self._set_tp_sl_order(coin, is_buy, quantity, take_profit_price, "tp")

    def _sync_positions_from_exchange(self):
        """
        从交易所同步现有持仓到本地跟踪

        这个方法在初始化时调用，用于处理机器人重启的情况。
        它会读取交易所的实际持仓，并将它们添加到 self.positions。

        注意：重启后我们无法获得原来的 TP/SL 订单 ID (sl_oid, tp_oid)，
        所以这些字段会是 None。这意味着重启后首次平仓时无法自动取消 TP/SL。
        """
        try:
            current_positions = self.get_current_positions()

            for pos in current_positions:
                coin = pos["coin"]
                self.positions[coin] = {
                    "coin": coin,
                    "is_buy": pos["is_buy"],
                    "quantity": pos["quantity"],
                    "entry_price": pos["entry_price"],
                    "leverage": pos["leverage"],
                    "stop_loss": pos.get("stop_loss"),
                    "profit_target": pos.get("profit_target"),
                    "sl_oid": None,  # 未知，重启后丢失
                    "tp_oid": None,  # 未知，重启后丢失
                    "entry_time": None  # 未知
                }

            if self.positions:
                print(f"📋 同步了 {len(self.positions)} 个现有持仓到本地跟踪")
                for coin in self.positions:
                    print(f"   - {coin}")

        except Exception as e:
            print(f"⚠️ 同步持仓失败: {e}")

    def get_current_positions(self) -> List[Dict[str, Any]]:
        """获取当前持仓"""
        try:
            user_state = self.info.user_state(self.exchange.wallet.address)
            
            if not user_state or 'assetPositions' not in user_state:
                return []
            
            # 调试：打印原始数据结构（只在有持仓时）
            if user_state.get('assetPositions'):
                import json
                print(f"\n🔍 调试: 获取到 {len(user_state['assetPositions'])} 个资产持仓")
                for i, asset_pos in enumerate(user_state['assetPositions'][:1]):  # 只打印第一个
                    print(f"原始持仓数据 [{i}]:")
                    print(json.dumps(asset_pos, indent=2, default=str))
            
            positions = []
            for asset_pos in user_state['assetPositions']:
                pos = asset_pos['position']
                coin = pos['coin']
                
                # 解析持仓信息 - 安全地处理可能为 None 的字段
                try:
                    size = abs(float(pos.get('szi', 0)))
                    if size > 0:
                        # 安全地获取入场价格
                        entry_px = pos.get('entryPx')
                        if entry_px is None:
                            continue  # 跳过无效持仓
                        entry_price = float(entry_px)
                        
                        # 安全地获取标记价格
                        mark_px = pos.get('markPx')
                        mark_price = float(mark_px) if mark_px is not None else entry_price
                        
                        # 安全地获取未实现盈亏
                        unrealized_pnl_val = pos.get('unrealizedPnl', 0)
                        unrealized_pnl = float(unrealized_pnl_val) if unrealized_pnl_val is not None else 0.0
                        
                        # 安全地获取杠杆
                        leverage_info = pos.get('leverage', {})
                        if isinstance(leverage_info, dict):
                            leverage = int(leverage_info.get('value', 1))
                        else:
                            leverage = 1
                        
                        # 安全地获取清算价格
                        liquidation_px_val = pos.get('liquidationPx', 0)
                        liquidation_px = float(liquidation_px_val) if liquidation_px_val is not None else 0.0
                        
                        position_info = {
                            "coin": coin,
                            "quantity": size,
                            "is_buy": float(pos.get('szi', 0)) > 0,
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
                
                except (ValueError, TypeError, KeyError) as e:
                    # 跳过无法解析的持仓
                    print(f"  ⚠️ 跳过无效持仓 {coin}: {e}")
                    continue
            
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

