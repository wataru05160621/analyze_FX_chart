#!/usr/bin/env python3
"""
Phase 1の分析結果からTradingViewアラート設定を自動生成
"""
import asyncio
from datetime import datetime
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv('.env.phase1')

from src.phase1_alert_system import SignalGenerator


def generate_tradingview_alert_config(signal, currency_pair="USD/JPY"):
    """TradingViewアラート設定を生成"""
    
    if signal['action'] == 'NONE':
        return None
    
    tv_symbol = currency_pair.replace('/', '')  # USD/JPY -> USDJPY
    
    config = {
        'symbol': f'FX:{tv_symbol}',
        'alerts': []
    }
    
    # エントリーアラート
    if signal['action'] == 'BUY':
        config['alerts'].append({
            'name': f'{currency_pair} 買いエントリー',
            'condition': f'{tv_symbol} >= {signal["entry_price"]}',
            'message': f'BUY {tv_symbol} @ {{{{close}}}} (Target: {signal["take_profit"]}, SL: {signal["stop_loss"]})',
            'webhook': True
        })
    else:  # SELL
        config['alerts'].append({
            'name': f'{currency_pair} 売りエントリー',
            'condition': f'{tv_symbol} <= {signal["entry_price"]}',
            'message': f'SELL {tv_symbol} @ {{{{close}}}} (Target: {signal["take_profit"]}, SL: {signal["stop_loss"]})',
            'webhook': True
        })
    
    # 損切りアラート
    if signal['action'] == 'BUY':
        config['alerts'].append({
            'name': f'{currency_pair} 損切り',
            'condition': f'{tv_symbol} <= {signal["stop_loss"]}',
            'message': f'STOP LOSS {tv_symbol} @ {{{{close}}}}',
            'webhook': True
        })
    else:  # SELL
        config['alerts'].append({
            'name': f'{currency_pair} 損切り',
            'condition': f'{tv_symbol} >= {signal["stop_loss"]}',
            'message': f'STOP LOSS {tv_symbol} @ {{{{close}}}}',
            'webhook': True
        })
    
    # 利確アラート
    if signal['action'] == 'BUY':
        config['alerts'].append({
            'name': f'{currency_pair} 利確',
            'condition': f'{tv_symbol} >= {signal["take_profit"]}',
            'message': f'TAKE PROFIT {tv_symbol} @ {{{{close}}}}',
            'webhook': True
        })
    else:  # SELL
        config['alerts'].append({
            'name': f'{currency_pair} 利確',
            'condition': f'{tv_symbol} <= {signal["take_profit"]}',
            'message': f'TAKE PROFIT {tv_symbol} @ {{{{close}}}}',
            'webhook': True
        })
    
    return config


def print_alert_instructions(config):
    """TradingView設定手順を表示"""
    
    print("\n" + "="*60)
    print("TradingViewアラート設定手順")
    print("="*60)
    
    print(f"\n1. TradingViewで {config['symbol']} チャートを開く")
    print("   https://jp.tradingview.com/chart/")
    
    webhook_url = os.environ.get('TRADINGVIEW_WEBHOOK_URL', 'https://your-domain.com/webhook')
    
    for i, alert in enumerate(config['alerts'], 1):
        print(f"\n【アラート {i}】{alert['name']}")
        print("2. アラートアイコン（時計マーク）をクリック")
        print("3. 以下を設定:")
        print(f"   - 条件: {alert['condition']}")
        print(f"   - 名前: {alert['name']}")
        print(f"   - メッセージ: {alert['message']}")
        if alert['webhook']:
            print(f"   - Webhook URL: {webhook_url}")
        print("4. 「作成」をクリック")
    
    print("\n" + "="*60)
    print("Pine Scriptでの自動化も可能です（上級者向け）")
    print("="*60)


def generate_pine_script(signal, currency_pair="USD/JPY"):
    """Pine Scriptを生成"""
    
    tv_symbol = currency_pair.replace('/', '')
    
    script = f'''// This source code is subject to the terms of the Mozilla Public License 2.0
// © Phase1_FX_Analysis

//@version=5
indicator("FX Alert - {currency_pair}", overlay=true)

// 設定値
entry_price = {signal['entry_price']}
stop_loss = {signal['stop_loss']}
take_profit = {signal['take_profit']}

// 価格レベルを描画
plot(entry_price, "Entry", color=color.blue, linewidth=2)
plot(stop_loss, "Stop Loss", color=color.red, linewidth=2)
plot(take_profit, "Take Profit", color=color.green, linewidth=2)

// 現在の状態
is_buy = "{signal['action']}" == "BUY"

// アラート条件
entry_triggered = is_buy ? close >= entry_price : close <= entry_price
sl_triggered = is_buy ? close <= stop_loss : close >= stop_loss
tp_triggered = is_buy ? close >= take_profit : close <= take_profit

// アラート
if entry_triggered and not entry_triggered[1]
    alert("{signal['action']} Entry: " + str.tostring(close), alert.freq_once_per_bar)

if sl_triggered and not sl_triggered[1]
    alert("Stop Loss Hit: " + str.tostring(close), alert.freq_once_per_bar)
    
if tp_triggered and not tp_triggered[1]
    alert("Take Profit Hit: " + str.tostring(close), alert.freq_once_per_bar)

// 背景色
bgcolor(entry_triggered ? color.new(color.blue, 90) : na)
'''
    
    return script


async def main():
    """メイン処理"""
    
    print("Phase 1 → TradingViewアラート設定ツール")
    print("="*60)
    
    # テスト用の分析テキスト
    test_analysis = """
    USD/JPYは145.50で強いブレイクアウトを確認しました。
    146.00を目標に、145.20を損切りラインとして
    買いエントリーを推奨します。
    """
    
    # シグナル生成
    generator = SignalGenerator()
    signal = generator.generate_trading_signal(test_analysis)
    
    print("\n【生成されたシグナル】")
    print(f"アクション: {signal['action']}")
    print(f"エントリー: {signal['entry_price']}")
    print(f"損切り: {signal['stop_loss']}")
    print(f"利確: {signal['take_profit']}")
    print(f"信頼度: {signal['confidence']:.1%}")
    
    if signal['action'] != 'NONE':
        # TradingView設定を生成
        config = generate_tradingview_alert_config(signal)
        
        # 設定手順を表示
        print_alert_instructions(config)
        
        # Pine Scriptを生成
        script = generate_pine_script(signal)
        
        # Pine Scriptをファイルに保存
        script_path = f"tradingview_alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pine"
        with open(script_path, 'w') as f:
            f.write(script)
        
        print(f"\nPine Scriptを保存しました: {script_path}")
        print("\nTradingViewで:")
        print("1. Pine エディタを開く")
        print("2. スクリプトをコピー&ペースト")
        print("3. 「チャートに追加」をクリック")
        print("4. アラートが自動的に設定されます")
    
    else:
        print("\n明確なシグナルがありません")


if __name__ == "__main__":
    asyncio.run(main())