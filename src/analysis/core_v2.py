"""Enhanced FX Analysis Core with schema compliance and quality gates."""

import uuid
import math
import os
from datetime import datetime
from typing import Dict, List, Tuple
import pytz
import pandas as pd

from src.utils.logger import get_logger
from src.guards.linguistic import LinguisticGuard

logger = get_logger(__name__)


class FXAnalyzerV2:
    """Enhanced FX market analyzer with quality gates and schema compliance."""
    
    # Setup types
    SETUPS = {
        "A": "Pattern Break",
        "B": "PB Pullback",
        "C": "Probe Reversal",
        "D": "Failed Break Reversal",
        "E": "Momentum Continuation",
        "F": "Range Scalp",
        "No-Trade": "No Trade"
    }
    
    def __init__(self, pair: str = "USDJPY"):
        """Initialize the enhanced analyzer."""
        self.pair = pair
        self.jst = pytz.timezone("Asia/Tokyo")
        self.linguistic_guard = LinguisticGuard()
        
        # EV calculation parameters (Beta distribution)
        self.setup_alpha = {"A": 3, "B": 2.5, "C": 2, "D": 2, "E": 3.5, "F": 1.5}
        self.setup_beta = {"A": 2, "B": 2, "C": 3, "D": 3, "E": 1.5, "F": 3}
        
    def analyze(self, data: Dict[str, pd.DataFrame]) -> Dict:
        """
        Main analysis entry point with schema compliance.
        
        Args:
            data: Dict mapping timeframe to DataFrame
            
        Returns:
            Schema-compliant analysis result
        """
        # Generate run_id with SESSION if available
        jst_now = datetime.now(self.jst)
        session = os.environ.get('SESSION', 'default')
        if session != 'default':
            run_id = f"{jst_now:%Y%m%d-%H%M}-{session}"
        else:
            run_id = str(uuid.uuid4())
        
        timestamp = jst_now.isoformat()
        
        # Initialize result structure
        result = {
            "run_id": run_id,
            "timestamp_jst": timestamp,
            "pair": self.pair,
            "timeframe": "5m",  # Primary timeframe
            "data_source": "twelvedata",
            "indicators": {},
            "setup": "No-Trade",
            "filters": {},
            "rationale": [],
            "confluence_count": 0,
            "no_trade_reasons": [],
            "advice_flags": [],
            "plan": {},
            "risk": {},
            "ev_R": 0.0,
            "confidence": "low",
            "charts": [],
            "notion": {},
            "status": "no-trade"
        }
        
        # Check data availability
        if not data or "5m" not in data or "1h" not in data:
            result["no_trade_reasons"].append("Missing timeframe data")
            return result
        
        df_5m = data["5m"]
        df_1h = data["1h"]
        
        if df_5m.empty or df_1h.empty:
            result["no_trade_reasons"].append("Empty dataframe")
            return result
        
        # Step 1: Calculate indicators for both timeframes
        indicators_5m = self.calculate_indicators(df_5m)
        indicators_1h = self.calculate_indicators(df_1h)
        
        # Primary indicators are from 5m
        result["indicators"] = indicators_5m
        
        # Step 2: Apply quality gates
        filters, gate_passed, no_trade_reasons = self.apply_quality_gates(indicators_5m)
        result["filters"] = filters
        
        # Track if this is a No-Trade situation but continue analysis
        is_no_trade = not gate_passed
        if is_no_trade:
            result["no_trade_reasons"] = no_trade_reasons
            result["status"] = "no-trade"
        
        # Step 3: Determine environment from 1h
        env_trend = self._determine_environment(indicators_1h)
        
        # Step 4: Determine setup based on environment and 5m data
        # For No-Trade, find the best hypothetical setup for analysis
        if is_no_trade:
            # Find what setup WOULD have been chosen if quality gates passed
            hypothetical_setup, hypothetical_rationale = self._determine_setup_v2(indicators_5m, env_trend, df_5m)
            result["setup"] = "No-Trade"
            result["hypothetical_setup"] = hypothetical_setup
            result["rationale"] = hypothetical_rationale
            result["analysis_mode"] = "hypothetical"
        else:
            setup, rationale = self._determine_setup_v2(indicators_5m, env_trend, df_5m)
            result["setup"] = setup
            result["rationale"] = rationale
            result["analysis_mode"] = "live"
        
        # Step 5: Calculate confluence count
        confluence_count = len(rationale)
        result["confluence_count"] = confluence_count
        
        # Step 6: Create trading plan (even for No-Trade as hypothetical)
        # Use hypothetical setup if No-Trade, otherwise use actual setup
        plan_setup = result.get("hypothetical_setup", result.get("setup"))
        
        if plan_setup and plan_setup != "No-Trade":
            plan = self._create_plan(plan_setup, indicators_5m)
            result["plan"] = plan
            
            # Step 7: Calculate EV
            ev_R = self._calculate_ev(plan_setup, confluence_count, plan)
            result["ev_R"] = round(ev_R, 2)
            
            # Step 8: Determine confidence
            if ev_R > 0.5 and confluence_count >= 4:
                confidence = "high"
            elif ev_R > 0 and confluence_count >= 3:
                confidence = "medium"
            else:
                confidence = "low"
            result["confidence"] = confidence
            
            # Step 9: Risk calculation
            result["risk"] = {
                "r_multiple": plan.get("tp_pips", 20) / plan.get("sl_pips", 10),
                "position_size": 0.01  # Default micro lot
            }
            
            # Mark hypothetical trades clearly
            if is_no_trade:
                result["plan"]["note"] = "HYPOTHETICAL - Quality gates not passed"
                result["hypothetical_ev_R"] = result["ev_R"]
                result["hypothetical_confidence"] = result["confidence"]
            else:
                result["status"] = "success"
        
        # Step 10: Apply linguistic guard to text fields
        result, advice_flags = self.linguistic_guard.check_dict(result)
        result["advice_flags"] = advice_flags
        
        # Step 11: Prepare Notion properties
        result["notion"] = self._prepare_notion_properties(result)
        
        logger.info(
            f"Analysis complete",
            run_id=run_id,
            setup=setup,
            confluence=confluence_count,
            ev_R=result["ev_R"],
            advice_flags=len(advice_flags)
        )
        
        return result
    
    def calculate_indicators(self, df: pd.DataFrame) -> Dict:
        """Calculate technical indicators."""
        if len(df) < 25:
            return {}
        
        # EMA calculation
        ema25 = df["close"].ewm(span=25, adjust=False).mean()
        current_ema = ema25.iloc[-1]
        
        # EMA slope (in degrees)
        if len(ema25) >= 10:
            ema_change = ema25.iloc[-1] - ema25.iloc[-10]
            ema_slope_deg = math.degrees(math.atan(ema_change / 10))
        else:
            ema_slope_deg = 0
        
        # ATR calculation
        high_low = df["high"] - df["low"]
        high_close = abs(df["high"] - df["close"].shift())
        low_close = abs(df["low"] - df["close"].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr20 = tr.rolling(window=20).mean().iloc[-1]
        
        # Convert ATR to pips
        if "JPY" in self.pair:
            atr20_pips = atr20 * 100
        else:
            atr20_pips = atr20 * 10000
        
        # Current price
        current_price = df["close"].iloc[-1]
        
        # Spread (simplified)
        spread = 0.1  # Default 0.1 pip
        
        # Round numbers
        round_numbers = self._find_round_numbers(current_price)
        
        # Build-up detection
        build_up = self._detect_buildup(df)
        
        return {
            "current_price": current_price,
            "ema25": current_ema,
            "ema25_slope_deg": round(ema_slope_deg, 2),
            "atr20": round(atr20_pips, 2),
            "spread": spread,
            "round_numbers": round_numbers,
            "build_up": build_up
        }
    
    def apply_quality_gates(self, indicators: Dict) -> Tuple[Dict, bool, List[str]]:
        """
        Apply quality gates (Q01).
        
        Returns:
            Tuple of (filters_dict, passed, no_trade_reasons)
        """
        filters = {
            "atr_ok": True,
            "spread_ok": True,
            "news_window_ok": True,
            "build_up_ok": True
        }
        no_trade_reasons = []
        
        # Gate 1: ATR check
        if indicators.get("atr20", 0) < 7:
            filters["atr_ok"] = False
            no_trade_reasons.append(f"ATR too low: {indicators.get('atr20', 0):.1f}p < 7p")
        
        # Gate 2: Spread check
        if indicators.get("spread", 0) > 2:
            filters["spread_ok"] = False
            no_trade_reasons.append(f"Spread too wide: {indicators.get('spread', 0):.1f}p > 2p")
        
        # Gate 3: News window - Only restrict the first 30 minutes of session opens
        # Since we run 30 minutes after open, we check for the actual volatile period
        current_time = datetime.now(self.jst)
        current_hour = current_time.hour
        current_minute = current_time.minute
        
        # Define actual volatile windows (first 30 minutes of each session)
        news_windows = [
            (9, 0, 9, 30),    # Tokyo: 9:00-9:30
            (15, 30, 16, 0),  # London: 15:30-16:00 (actual London open time)
            (22, 0, 22, 30),  # NY: 22:00-22:30
        ]
        
        in_news_window = False
        for start_h, start_m, end_h, end_m in news_windows:
            if start_h == end_h:
                if current_hour == start_h and start_m <= current_minute < end_m:
                    in_news_window = True
                    break
            else:  # Handles London case (15:30-16:00)
                if (current_hour == start_h and current_minute >= start_m) or \
                   (current_hour == end_h and current_minute < end_m):
                    in_news_window = True
                    break
        
        if in_news_window:
            filters["news_window_ok"] = False
            no_trade_reasons.append("Within news window (first 30min of session open)")
        
        # Gate 4: Build-up quality (need 2/3 conditions)
        build_up = indicators.get("build_up", {})
        build_up_score = 0
        if build_up.get("width_pips", 0) >= 10:
            build_up_score += 1
        if build_up.get("bars", 0) >= 10:
            build_up_score += 1
        if build_up.get("ema_inside", False):
            build_up_score += 1
        
        if build_up_score < 2:
            filters["build_up_ok"] = False
            no_trade_reasons.append(f"Build-up quality insufficient: {build_up_score}/3")
        
        # Overall gate decision
        gate_passed = all(filters.values())
        
        return filters, gate_passed, no_trade_reasons
    
    def _determine_environment(self, indicators_1h: Dict) -> str:
        """Determine market environment from 1h timeframe."""
        slope = indicators_1h.get("ema25_slope_deg", 0)
        
        if slope > 15:
            return "strong_bullish"
        elif slope > 5:
            return "bullish"
        elif slope < -15:
            return "strong_bearish"
        elif slope < -5:
            return "bearish"
        else:
            return "ranging"
    
    def _determine_setup_v2(self, indicators: Dict, env_trend: str, df: pd.DataFrame) -> Tuple[str, List[str]]:
        """
        Enhanced setup determination with decision tree (Q01).
        """
        rationale = []
        setup = "No-Trade"
        
        # Get build-up info
        build_up = indicators.get("build_up", {})
        ema_slope = indicators.get("ema25_slope_deg", 0)
        atr = indicators.get("atr20", 0)
        
        # Decision tree based on environment
        if env_trend in ["strong_bullish", "bullish"]:
            # Look for continuation setups
            if build_up.get("width_pips", 0) > 15 and build_up.get("bars", 0) > 15:
                setup = "A"  # Pattern Break
                rationale.append("Strong build-up in bullish environment")
                rationale.append(f"Build-up width: {build_up.get('width_pips', 0):.1f}p")
                rationale.append(f"1h trend: {env_trend}")
            elif ema_slope > 10:
                setup = "E"  # Momentum Continuation
                rationale.append(f"Strong EMA slope: {ema_slope:.1f}°")
                rationale.append(f"1h trend alignment: {env_trend}")
                rationale.append(f"ATR supportive: {atr:.1f}p")
            elif self._check_pullback(df):
                setup = "B"  # PB Pullback
                rationale.append("Pullback to EMA in uptrend")
                rationale.append(f"1h bullish environment: {env_trend}")
                rationale.append("Price action confirms support")
                
        elif env_trend in ["strong_bearish", "bearish"]:
            # Look for reversal or short setups
            if self._check_failed_break(df):
                setup = "D"  # Failed Break Reversal
                rationale.append("Failed break detected")
                rationale.append(f"1h bearish environment: {env_trend}")
                rationale.append("Rejection at resistance")
            elif build_up.get("width_pips", 0) > 15:
                setup = "C"  # Probe Reversal
                rationale.append("Potential reversal setup")
                rationale.append(f"Build-up present: {build_up.get('width_pips', 0):.1f}p")
                rationale.append(f"1h trend weakening: {env_trend}")
                
        else:  # Ranging
            if build_up.get("width_pips", 0) > 10 and build_up.get("width_pips", 0) < 20:
                setup = "F"  # Range Scalp
                rationale.append("Range-bound conditions")
                rationale.append(f"Tight build-up: {build_up.get('width_pips', 0):.1f}p")
                rationale.append("1h ranging environment")
        
        # Add common supporting factors
        if setup != "No-Trade":
            # Check round number proximity
            current_price = indicators.get("current_price", 0)
            round_numbers = indicators.get("round_numbers", [])
            for rn in round_numbers:
                distance_pips = abs(current_price - rn) * (100 if "JPY" in self.pair else 10000)
                if distance_pips < 20:
                    rationale.append(f"Near round number: {rn:.2f}")
                    break
            
            # Add ATR context
            if atr > 10:
                rationale.append(f"Favorable volatility: {atr:.1f}p")
        
        return setup, rationale
    
    def _check_pullback(self, df: pd.DataFrame) -> bool:
        """Check if price pulled back to EMA."""
        if len(df) < 25:
            return False
        
        ema25 = df["close"].ewm(span=25, adjust=False).mean()
        recent_low = df["low"].iloc[-5:].min()
        current_close = df["close"].iloc[-1]
        ema_current = ema25.iloc[-1]
        
        # Pullback condition: recent low touched EMA and bounced
        return (recent_low <= ema_current * 1.001 and 
                current_close > ema_current)
    
    def _check_failed_break(self, df: pd.DataFrame) -> bool:
        """Check for failed breakout pattern."""
        if len(df) < 20:
            return False
        
        recent_high = df["high"].iloc[-20:-5].max()
        spike_high = df["high"].iloc[-5:].max()
        current_close = df["close"].iloc[-1]
        
        # Failed break: spike above recent high but close below
        return (spike_high > recent_high * 1.002 and 
                current_close < recent_high)
    
    def _create_plan(self, setup: str, indicators: Dict) -> Dict:
        """Create trading plan based on setup."""
        atr = indicators.get("atr20", 10)
        
        # Base 20/10 bracket with ATR adjustment
        base_tp = 20
        base_sl = 10
        
        # Adjust by ±25% based on ATR
        if atr > 15:
            tp_pips = base_tp * 1.25
            sl_pips = base_sl * 1.25
        elif atr < 10:
            tp_pips = base_tp * 0.75
            sl_pips = base_sl * 0.75
        else:
            tp_pips = base_tp
            sl_pips = base_sl
        
        # Setup-specific adjustments
        if setup == "A":  # Pattern Break
            entry = "Break of build-up high"
            timeout = 60
        elif setup == "B":  # Pullback
            entry = "Bounce from EMA25"
            timeout = 45
        elif setup == "C":  # Probe Reversal
            entry = "Rejection at resistance"
            timeout = 30
        elif setup == "D":  # Failed Break
            entry = "Failed break confirmation"
            timeout = 30
        elif setup == "E":  # Momentum
            entry = "Momentum continuation"
            timeout = 90
        elif setup == "F":  # Range Scalp
            entry = "Range boundary"
            tp_pips = 10  # Smaller target for scalp
            timeout = 30
        else:
            entry = "No entry"
            timeout = 0
        
        return {
            "entry": entry,
            "tp_pips": round(tp_pips, 1),
            "sl_pips": round(sl_pips, 1),
            "timeout_min": timeout
        }
    
    def _calculate_ev(self, setup: str, confluence: int, plan: Dict) -> float:
        """
        Calculate expected value using Beta distribution (Q02).
        """
        if setup == "No-Trade":
            return 0.0
        
        # Get setup-specific alpha/beta
        alpha = self.setup_alpha.get(setup, 2)
        beta = self.setup_beta.get(setup, 2)
        
        # Calculate base win rate from Beta distribution
        base_win_rate = alpha / (alpha + beta)
        
        # Apply EWMA adjustment (simplified - would track historical)
        ewma_factor = 0.9
        adjusted_win_rate = base_win_rate * ewma_factor
        
        # Apply confluence adjustment
        if confluence < 3:
            adjusted_win_rate *= 0.8  # Reduce for low confluence
        elif confluence >= 5:
            adjusted_win_rate *= 1.1  # Boost for high confluence
        
        # Ensure win rate is between 0 and 1
        adjusted_win_rate = max(0.1, min(0.9, adjusted_win_rate))
        
        # Calculate EV
        tp_pips = plan.get("tp_pips", 20)
        sl_pips = plan.get("sl_pips", 10)
        r_multiple = tp_pips / sl_pips
        
        ev_R = adjusted_win_rate * r_multiple - (1 - adjusted_win_rate)
        
        return ev_R
    
    def _find_round_numbers(self, price: float, range_pips: int = 100) -> List[float]:
        """Find nearby round numbers."""
        if "JPY" in self.pair:
            # Round to nearest 0.50
            base = round(price / 0.5) * 0.5
            levels = []
            for i in range(-2, 3):
                level = base + (i * 0.5)
                if abs(level - price) * 100 <= range_pips:
                    levels.append(round(level, 2))
            return levels
        else:
            # For other pairs
            base = round(price / 0.005) * 0.005
            levels = []
            for i in range(-2, 3):
                level = base + (i * 0.005)
                if abs(level - price) * 10000 <= range_pips:
                    levels.append(round(level, 5))
            return levels
    
    def _detect_buildup(self, df: pd.DataFrame) -> Dict:
        """Detect build-up pattern."""
        if len(df) < 20:
            return {"width_pips": 0, "bars": 0, "ema_inside": False}
        
        recent = df.iloc[-20:]
        
        high_range = recent["high"].max()
        low_range = recent["low"].min()
        width_pips = (high_range - low_range) * (100 if "JPY" in self.pair else 10000)
        
        # Count consecutive bars in range
        bars_in_range = 0
        for i in range(len(recent) - 1, -1, -1):
            if recent["high"].iloc[i] <= high_range and recent["low"].iloc[i] >= low_range:
                bars_in_range += 1
            else:
                break
        
        # Check if EMA is inside range
        ema25 = recent["close"].ewm(span=25, adjust=False).mean()
        ema_inside = False
        if len(ema25) > 0:
            ema_current = ema25.iloc[-1]
            ema_inside = low_range <= ema_current <= high_range
        
        return {
            "width_pips": round(width_pips, 1),
            "bars": int(bars_in_range),  # Ensure it's a regular int
            "ema_inside": bool(ema_inside)  # Ensure it's a regular bool
        }
    
    def _prepare_notion_properties(self, analysis: Dict) -> Dict:
        """Prepare Notion database properties."""
        setup_name = self.SETUPS.get(analysis["setup"], "No-Trade")
        
        return {
            "Name": f"{self.pair} - {setup_name} - {datetime.now(self.jst).strftime('%Y-%m-%d %H:%M')}",
            "Date": datetime.now(self.jst).isoformat(),
            "Currency": self.pair,
            "Timeframe": analysis["timeframe"],
            "Setup": setup_name,
            "Confidence": analysis["confidence"],
            "EV_R": analysis["ev_R"],
            "EntryType": analysis.get("plan", {}).get("entry", ""),
            "TP_pips": analysis.get("plan", {}).get("tp_pips", 0),
            "SL_pips": analysis.get("plan", {}).get("sl_pips", 0),
            "Status": "Pending" if analysis["setup"] != "No-Trade" else "No-Trade",
            "Summary": " | ".join(analysis["rationale"][:3]) if analysis["rationale"] else "No trade opportunity",
            "RunId": analysis["run_id"],
            "Charts": []  # Will be filled by chart URLs
        }