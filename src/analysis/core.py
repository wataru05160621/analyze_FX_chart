"""Core FX analysis logic."""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import ta
import pytz

from src.utils.config import config
from src.utils.logger import get_logger

logger = get_logger(__name__)

class FXAnalyzer:
    """FX price action analyzer."""
    
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
    
    def __init__(self, pair: str = None):
        """Initialize analyzer."""
        self.pair = pair or config.pair
        self.jst = pytz.timezone("Asia/Tokyo")
        
    def calculate_indicators(self, df: pd.DataFrame) -> Dict:
        """
        Calculate technical indicators.
        
        Args:
            df: OHLCV DataFrame
            
        Returns:
            Dict with calculated indicators
        """
        # Calculate EMA 25
        df["ema25"] = ta.trend.ema_indicator(df["close"], window=25)
        
        # Calculate ATR 20
        df["atr20"] = ta.volatility.average_true_range(
            df["high"], df["low"], df["close"], window=20
        )
        
        # Calculate EMA slope (in degrees)
        if len(df) > 1:
            ema_diff = df["ema25"].iloc[-1] - df["ema25"].iloc[-5] if len(df) > 5 else 0
            price_range = df["close"].iloc[-20:].max() - df["close"].iloc[-20:].min() if len(df) > 20 else 1
            ema_slope_deg = np.degrees(np.arctan(ema_diff / (price_range * 0.1))) if price_range > 0 else 0
        else:
            ema_slope_deg = 0
            
        # Current values
        current_price = df["close"].iloc[-1]
        current_atr = df["atr20"].iloc[-1] if "atr20" in df else 0
        current_ema = df["ema25"].iloc[-1] if "ema25" in df else current_price
        
        # Calculate spread (simplified - would need real-time bid/ask)
        spread = 0.1  # Default 0.1 pip
        
        # Find round numbers
        round_numbers = self._find_round_numbers(current_price)
        
        # Detect build-up
        build_up = self._detect_buildup(df)
        
        return {
            "current_price": current_price,
            "ema25": current_ema,
            "ema25_slope_deg": round(ema_slope_deg, 2),
            "atr20": round(current_atr, 2),
            "spread": spread,
            "round_numbers": round_numbers,
            "build_up": build_up
        }
    
    def _find_round_numbers(self, price: float, range_pips: int = 100) -> List[float]:
        """Find nearby round numbers (00/50 levels)."""
        # For USDJPY
        if "JPY" in self.pair:
            # Round to nearest 0.50
            base = round(price / 0.5) * 0.5
            levels = []
            for i in range(-2, 3):
                level = base + (i * 0.5)
                if abs(level - price) * 100 <= range_pips:  # Convert to pips
                    levels.append(round(level, 2))
            return levels
        else:
            # For other pairs (4 decimal places)
            base = round(price / 0.005) * 0.005  
            levels = []
            for i in range(-2, 3):
                level = base + (i * 0.005)
                if abs(level - price) * 10000 <= range_pips:
                    levels.append(round(level, 5))
            return levels
    
    def _detect_buildup(self, df: pd.DataFrame) -> Dict:
        """
        Detect build-up pattern.
        
        Returns:
            Dict with build-up characteristics
        """
        if len(df) < 20:
            return {"width_pips": 0, "bars": 0, "ema_inside": False}
        
        # Look at last 20 bars
        recent = df.iloc[-20:]
        
        # Calculate range
        high_range = recent["high"].max()
        low_range = recent["low"].min()
        width_pips = (high_range - low_range) * (100 if "JPY" in self.pair else 10000)
        
        # Count bars in range
        bars_in_range = 0
        for i in range(len(recent) - 1, -1, -1):
            if recent["high"].iloc[i] <= high_range and recent["low"].iloc[i] >= low_range:
                bars_in_range += 1
            else:
                break
        
        # Check if EMA is inside the range
        ema_inside = False
        if "ema25" in recent.columns:
            ema_values = recent["ema25"].dropna()
            if len(ema_values) > 0:
                ema_inside = (ema_values >= low_range).all() and (ema_values <= high_range).all()
        
        return {
            "width_pips": round(width_pips, 1),
            "bars": bars_in_range,
            "ema_inside": ema_inside
        }
    
    def determine_setup(self, indicators: Dict, timeframe: str) -> Tuple[str, List[str]]:
        """
        Determine trading setup based on indicators.
        
        Args:
            indicators: Calculated indicators
            timeframe: Timeframe being analyzed
            
        Returns:
            Tuple of (setup_type, rationale_list)
        """
        rationale = []
        
        # Check filters first
        filters_passed, filter_reasons = self._check_filters(indicators)
        if not filters_passed:
            return "No-Trade", filter_reasons
        
        # Analyze market conditions
        ema_slope = indicators["ema25_slope_deg"]
        build_up = indicators["build_up"]
        current_price = indicators["current_price"]
        ema25 = indicators["ema25"]
        
        # Trend determination
        if abs(ema_slope) > 30:
            trend = "strong_trend"
            rationale.append(f"Strong {'uptrend' if ema_slope > 0 else 'downtrend'} (EMA slope: {ema_slope}°)")
        elif abs(ema_slope) > 10:
            trend = "mild_trend"
            rationale.append(f"Mild {'uptrend' if ema_slope > 0 else 'downtrend'} (EMA slope: {ema_slope}°)")
        else:
            trend = "range"
            rationale.append(f"Range-bound market (EMA slope: {ema_slope}°)")
        
        # Build-up quality check
        if build_up["width_pips"] >= 10 and build_up["bars"] >= 10:
            if build_up["ema_inside"]:
                rationale.append(f"Quality build-up detected ({build_up['width_pips']}p x {build_up['bars']} bars, EMA inside)")
                
                # Determine setup based on position
                if current_price > ema25 and ema_slope > 10:
                    return "A", rationale + ["Price above rising EMA - Pattern Break setup"]
                elif current_price < ema25 and ema_slope < -10:
                    return "A", rationale + ["Price below falling EMA - Pattern Break setup"]
                else:
                    return "C", rationale + ["Build-up near EMA - Probe Reversal setup"]
            else:
                rationale.append(f"Build-up detected but EMA not inside ({build_up['width_pips']}p x {build_up['bars']} bars)")
        
        # Pullback detection
        if trend in ["strong_trend", "mild_trend"]:
            price_ema_dist = abs(current_price - ema25) / indicators["atr20"] if indicators["atr20"] > 0 else 0
            if price_ema_dist < 0.5:
                return "B", rationale + ["Price near EMA in trend - Pullback setup"]
        
        # Range scalp
        if trend == "range" and indicators["atr20"] >= 7:
            return "F", rationale + ["Range market with sufficient volatility - Range Scalp setup"]
        
        # Default to no trade if no clear setup
        return "No-Trade", rationale + ["No clear setup identified"]
    
    def _check_filters(self, indicators: Dict) -> Tuple[bool, List[str]]:
        """
        Check if trade filters pass.
        
        Returns:
            Tuple of (all_passed, failure_reasons)
        """
        failures = []
        
        # ATR filter
        if indicators["atr20"] < 7:
            failures.append(f"ATR too low ({indicators['atr20']}p < 7p minimum)")
        
        # Spread filter  
        if indicators["spread"] > 2:
            failures.append(f"Spread too wide ({indicators['spread']}p > 2p maximum)")
        
        # Round number proximity (should be at least 8 pips away)
        current_price = indicators["current_price"]
        for level in indicators["round_numbers"]:
            distance_pips = abs(level - current_price) * (100 if "JPY" in self.pair else 10000)
            if distance_pips < 8:
                failures.append(f"Too close to round number {level} ({distance_pips:.1f}p < 8p minimum)")
                break
        
        return len(failures) == 0, failures
    
    def analyze(self, data: Dict[str, pd.DataFrame]) -> Dict:
        """
        Perform complete analysis on multi-timeframe data.
        
        Args:
            data: Dict mapping timeframe to DataFrame
            
        Returns:
            Analysis result dict
        """
        run_id = str(uuid.uuid4())
        timestamp = datetime.now(self.jst).isoformat()
        
        results = {
            "run_id": run_id,
            "timestamp_jst": timestamp,
            "pair": self.pair,
            "timeframes": {},
            "final_setup": "No-Trade",
            "confidence": "low",
            "ev_R": 0.0,
            "status": "analyzed"
        }
        
        all_rationale = []
        setups_found = []
        
        # Analyze each timeframe
        for timeframe, df in data.items():
            if df is None or df.empty:
                logger.warning(f"No data for {timeframe}")
                continue
                
            indicators = self.calculate_indicators(df)
            setup, rationale = self.determine_setup(indicators, timeframe)
            
            results["timeframes"][timeframe] = {
                "indicators": indicators,
                "setup": setup,
                "rationale": rationale
            }
            
            all_rationale.extend([f"[{timeframe}] {r}" for r in rationale])
            if setup != "No-Trade":
                setups_found.append((timeframe, setup))
        
        # Determine final setup (both timeframes should align)
        if len(setups_found) == 2 and setups_found[0][1] == setups_found[1][1]:
            results["final_setup"] = setups_found[0][1]
            results["confidence"] = "high"
            results["ev_R"] = 1.5  # Simplified EV calculation
            all_rationale.append(f"Both timeframes align on {self.SETUPS[results['final_setup']]} setup")
        elif len(setups_found) == 1:
            results["final_setup"] = setups_found[0][1]
            results["confidence"] = "medium"
            results["ev_R"] = 0.8
            all_rationale.append(f"Only {setups_found[0][0]} shows {self.SETUPS[results['final_setup']]} setup")
        else:
            all_rationale.append("No valid setup found or timeframes disagree")
        
        results["rationale"] = all_rationale
        
        # Add plan if trade setup found
        if results["final_setup"] != "No-Trade":
            results["plan"] = self._create_trade_plan(results)
        else:
            results["plan"] = {"action": "wait", "reason": "No valid setup"}
        
        # Risk assessment
        results["risk"] = {
            "market_risk": "normal",
            "execution_risk": "low",
            "max_loss_R": 1.0
        }
        
        logger.info(
            "Analysis complete",
            run_id=run_id,
            setup=results["final_setup"],
            confidence=results["confidence"]
        )
        
        return results
    
    def _create_trade_plan(self, analysis: Dict) -> Dict:
        """Create trade plan based on analysis."""
        # Get 5m indicators for precise levels
        if "5m" in analysis["timeframes"]:
            indicators = analysis["timeframes"]["5m"]["indicators"]
        else:
            indicators = list(analysis["timeframes"].values())[0]["indicators"]
        
        current_price = indicators["current_price"]
        atr = indicators["atr20"]
        
        # 20/10 bracket with ATR adjustment
        sl_distance = 20 * (1 + (atr - 10) * 0.025) if atr > 10 else 20
        tp_distance = 10 * (1 + (atr - 10) * 0.025) if atr > 10 else 10
        
        # Convert to price (accounting for JPY pairs)
        pip_value = 0.01 if "JPY" in self.pair else 0.0001
        
        return {
            "entry": round(current_price, 3 if "JPY" in self.pair else 5),
            "stop_loss": round(current_price - sl_distance * pip_value, 3 if "JPY" in self.pair else 5),
            "take_profit": round(current_price + tp_distance * pip_value, 3 if "JPY" in self.pair else 5),
            "position_size": "1R",
            "notes": f"{self.SETUPS[analysis['final_setup']]} setup with {analysis['confidence']} confidence"
        }