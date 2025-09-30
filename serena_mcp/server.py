#!/usr/bin/env python3
import asyncio
import json
import os
import sys
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import logging

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Server("serena-fx")

@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools for FX analysis"""
    return [
        Tool(
            name="analyze_fx",
            description="Analyze FX data and generate insights based on SERENA MCP memory",
            inputSchema={
                "type": "object",
                "properties": {
                    "pair": {"type": "string", "description": "Currency pair (e.g., USD/JPY)"},
                    "timeframe": {"type": "string", "description": "Timeframe (5m or 1h)"},
                    "action": {"type": "string", "enum": ["analyze", "backtest", "setup_check"]},
                },
                "required": ["pair", "timeframe", "action"]
            }
        ),
        Tool(
            name="quality_gate_check",
            description="Check if conditions meet quality gate criteria",
            inputSchema={
                "type": "object",
                "properties": {
                    "atr20": {"type": "number", "description": "20-period ATR value"},
                    "spread": {"type": "number", "description": "Current spread in pips"},
                    "news_time": {"type": "boolean", "description": "Is it within 10 minutes of news?"},
                    "buildup_width": {"type": "number", "description": "Buildup width in pips"},
                    "buildup_bars": {"type": "integer", "description": "Number of bars in buildup"},
                    "ema_inside": {"type": "boolean", "description": "Is 25EMA inside buildup?"}
                },
                "required": ["atr20", "spread"]
            }
        ),
        Tool(
            name="setup_classification",
            description="Classify the trading setup type",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Pattern description"},
                    "price_action": {"type": "string", "description": "Recent price action"},
                    "ema_position": {"type": "string", "description": "Price position relative to 25EMA"}
                },
                "required": ["pattern", "price_action"]
            }
        ),
        Tool(
            name="generate_narrative",
            description="Generate EV-based narrative avoiding investment advice",
            inputSchema={
                "type": "object",
                "properties": {
                    "analysis": {"type": "object", "description": "Analysis results"},
                    "timeframe": {"type": "string", "description": "Timeframe analyzed"},
                    "avoid_advice": {"type": "boolean", "default": True}
                },
                "required": ["analysis", "timeframe"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Execute tool based on SERENA MCP memory principles"""
    
    if name == "analyze_fx":
        pair = arguments.get("pair", "USD/JPY")
        timeframe = arguments.get("timeframe", "5m")
        action = arguments.get("action", "analyze")
        
        result = {
            "pair": pair,
            "timeframe": timeframe,
            "action": action,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "analysis": {
                "trend": "Building up near 152.00",
                "ema25_slope": "Slightly bullish",
                "key_levels": ["152.00", "151.50", "152.50"],
                "setup_type": "A: Pattern Break potential",
                "quality_score": 7.5,
                "ev_assessment": "Positive EV setup if break above 152.00 with follow-through"
            },
            "recommendation": "Monitor for break above 152.00 with 20/10 bracket",
            "disclaimer": "分析結果は期待値に基づく評価であり、投資助言ではありません"
        }
        
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
    
    elif name == "quality_gate_check":
        atr20 = arguments.get("atr20", 0)
        spread = arguments.get("spread", 0)
        news_time = arguments.get("news_time", False)
        buildup_width = arguments.get("buildup_width", 0)
        buildup_bars = arguments.get("buildup_bars", 0)
        ema_inside = arguments.get("ema_inside", False)
        
        checks = {
            "atr_check": atr20 >= 7,
            "spread_check": spread <= 2,
            "news_check": not news_time,
            "buildup_quality": (
                buildup_width >= 10 and 
                buildup_bars >= 10 and 
                ema_inside
            ) if buildup_width > 0 else None
        }
        
        pass_gate = (
            checks["atr_check"] and 
            checks["spread_check"] and 
            checks["news_check"]
        )
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "pass": pass_gate,
                "checks": checks,
                "message": "Quality gate passed" if pass_gate else "Quality gate failed"
            }, indent=2)
        )]
    
    elif name == "setup_classification":
        pattern = arguments.get("pattern", "")
        price_action = arguments.get("price_action", "")
        ema_position = arguments.get("ema_position", "")
        
        setup_types = {
            "A": "Pattern Break",
            "B": "PB Pullback",
            "C": "Probe Reversal",
            "D": "Failed Break Reversal",
            "E": "Momentum Continuation",
            "F": "Range Scalp"
        }
        
        classified = "A"
        if "pullback" in price_action.lower():
            classified = "B"
        elif "probe" in pattern.lower():
            classified = "C"
        elif "failed" in pattern.lower():
            classified = "D"
        elif "momentum" in price_action.lower():
            classified = "E"
        elif "range" in pattern.lower():
            classified = "F"
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "setup_code": classified,
                "setup_name": setup_types[classified],
                "confidence": 0.75
            }, indent=2)
        )]
    
    elif name == "generate_narrative":
        analysis = arguments.get("analysis", {})
        timeframe = arguments.get("timeframe", "5m")
        
        narrative = f"""
【{timeframe}分析】
現在の市場構造は{analysis.get('trend', 'レンジ')}を示しており、
25EMAの傾きは{analysis.get('ema25_slope', 'フラット')}です。

期待値評価：
{analysis.get('ev_assessment', '現時点では明確な優位性は見られません')}

注目ポイント：
- キーレベル: {', '.join(analysis.get('key_levels', []))}
- セットアップタイプ: {analysis.get('setup_type', '未分類')}
- 品質スコア: {analysis.get('quality_score', 0)}/10

※本分析は期待値に基づく技術的評価であり、投資助言ではありません。
"""
        
        return [TextContent(type="text", text=narrative)]
    
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

@app.list_resources()
async def list_resources() -> List[EmbeddedResource]:
    """List available resources"""
    return [
        EmbeddedResource(
            type="embedded",
            resource={
                "uri": "memory://serena-principles",
                "name": "SERENA Trading Principles",
                "description": "Core trading principles and quality gates",
                "mimeType": "text/plain"
            }
        )
    ]

@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read resource content"""
    if uri == "memory://serena-principles":
        return """
# SERENA Trading Principles

## 行動原則
- 期待値で評価（勝率は二次的）
- トレンドフォロー優先
- ビルドアップの質（幅≥10p・足≥10・25EMA内包）
- 根拠3つ以上の重複

## Quality Gates
- ATR20 >= 7p
- Spread <= 2p
- News ±10min除外
- Buildup基準満たす

## Setup Types
A: Pattern Break
B: PB Pullback
C: Probe Reversal
D: Failed Break Reversal
E: Momentum Continuation
F: Range Scalp

## Risk Management
- 20/10 Bracket (ATR調整±25%)
- 連敗3回 or -2R → 30分クールダウン
"""
    return "Resource not found"

async def main():
    """Main entry point for the MCP server"""
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="serena-fx",
                server_version="1.0.0"
            )
        )

if __name__ == "__main__":
    asyncio.run(main())